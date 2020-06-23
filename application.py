import os, requests
import hashlib

from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from flask_session import Session
from tempfile import mkdtemp
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from werkzeug.security import check_password_hash, generate_password_hash
from helper import login_required

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#  WTF registeration Form
class RegisterForm(Form):
    name = StringField('Name', validators=[validators.DataRequired(), validators.Length(min=4, max=25)])
    username = StringField('Username',validators= [validators.DataRequired(), validators.Length(min=4, max=25)])
    email = StringField('Email Address', validators=[validators.DataRequired(), validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')

# Index Route
@app.route("/")
def index():

    return render_template('index.html')

# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register new user using RegisterForm"""

    # Forget any user_id
    session.clear()

    # Create Form with field
    form = RegisterForm(request.form)

    # If user submit form with validate data
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data.lower()
        username = form.username.data.lower()
        password = generate_password_hash(form.password.data)

        # Query DB for Username and email
        data = db.execute("SELECT username, email FROM users").fetchall()

        # Check if email or username already exist
        if data:
            for i in range(len(data)):
                if data[i].email == email:
                    error = "Email Already Exist"
                    return render_template("register.html", form=form, error=error)

                elif data[i].username == username:
                    error = "username Already Exist"
                    return render_template("register.html", form=form, error=error)

        #  Execute query  by insert into DB new username and password
        db.execute("INSERT INTO users (name, email, username, password) VALUES (:name, :email, :username, :password)",
                {"name": name, "email": email, "username": username, "password": password})

        # Commit to DB
        db.commit()

        # Close the DB
        db.close()

        # Flashing after complete transaction and Redirector
        flash("You are now Registered and you can log in", "success")
        return redirect(url_for('login'))

    return render_template('register.html', form = form)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login function for existing user with validate Credentials data."""

    # Forget any user_id
    session.clear()

    # Check if user access method
    if request.method == 'POST':

        # Get user data from Form
        username = request.form['username'].lower()
        password_enter = request.form['password']

        # Get username and password form database
        user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()

        # If username exists and password is correct save current in Session
        if user != None:
            password = user.password
            if check_password_hash(password, password_enter):
                session['logged_in'] = True
                session['username'] = username
                session["user_id"] = user.id

                # CLose DB and redirect to search page
                db.close()
                return redirect(url_for('dashboard'))

            # Else if username or password or both are wrong
            else:
                error = 'Invalid Lgoin Credentials!'
                return render_template('login.html', error=error)

        # If user does not exists
        else:
            error = 'Username Not Found!'
            return render_template('login.html', error=error)

    # If user access through Get Route
    return render_template('login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    """Logout remove user from session and redirect to login page"""

    session.clear()
    flash("You are now logged out, Thanks!", "success")

    return redirect(url_for('login'))

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Search route
@app.route('/search', methods=['POST'])
@login_required
def search():
    """ Get book details When receive xml request from js with search query"""

    # Check book isbn or title or author was provided if
    if not request.form.get("searchText"):
        error = "You must provide a book details for search!"
        return jsonify({"success": False, "error":error})

    # Store query wildcard to search with any part of book detail
    query = "%"+request.form.get("searchText")+"%"

    # Query DB for any match of book or books
    books_res = db.execute("SELECT * FROM books WHERE isbn LIKE :query OR title LIKE :query OR author LIKE :query",
                            {"query": query}).fetchall()

    # If nothing found
    if len(books_res) == 0:
        error = "We can't find any match. Please try with other Title, Author or ISBN!"
        return jsonify({"success": False, "error":error})

    # convert list to direction and return to js to display
    books = [dict(row) for row in books_res]
    return jsonify({"success": True, "books": books})

# Bookpage route
@app.route('/bookpage/<isbn>' ,methods=['GET', 'POST'])
@login_required
def bookpage(isbn):

    # Post review in DB
    if request.method == "POST":
        rating = int(request.form.get("rating"))
        review = request.form.get("review")

        check_review = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_isbn = :book_isbn",
                    {"user_id": session["user_id"],
                     "book_isbn": isbn})

        if check_review.rowcount == 1:

            return redirect("/bookpage/" + isbn)
        else:
            db.execute("INSERT INTO reviews (review, rating, user_id, book_isbn) VALUES (:review, :rating, :user_id, :book_isbn)",
            {"review": review,
            "rating": rating,
            "user_id": session["user_id"],
            "book_isbn": isbn})

            db.commit()
            check = False

            return redirect("/bookpage/" + isbn)

    # User access the page through GET
    else:
        # Active to check user comment or not
        check = True

        # Query DB for any match
        book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                                {"isbn": isbn}).fetchone()

        """GoodReads API to get ratings_count and average_rating value"""
        res = requests.get("https://www.goodreads.com/book/review_counts.json",
                           params={"key": os.getenv("API_KEY"), "isbns": isbn}).json()["books"][0]
        ratings_count = res['work_ratings_count']
        average_rating = res['average_rating']

        # Here for star of the book from API to fill width in 100%
        starPercentage = (float(average_rating) / 5) * 100;
        starPercentageRounded = round(starPercentage / 10) * 10;

        # Query the DB for comments of all users
        reviews = db.execute("SELECT username, review, rating, publish_date FROM users INNER JOIN reviews ON users.id = reviews.user_id WHERE book_isbn = :isbn",{"isbn": isbn}).fetchall()

        # Here to check if current user already commment then set active
        for review in reviews:
            if session['username'].lower() == review[0]:
                check = False

        return render_template('bookpage.html', book=book, ratings_count=ratings_count , average_rating=average_rating,reviews=reviews, check = check, starPercentageRounded=starPercentageRounded)

# Api route for get informatioon about any book
@app.route('/api/<string:isbn>')
def book_api(isbn):

    # Query DB for any match
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

    # Make sure book exists
    if book is None:
        return jsonify({"Error": "Invalid book isbn"}), 404

    """GoodReads API"""
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": os.getenv("API_KEY"), "isbns": isbn}).json()["books"][0]

    return jsonify({
        "title" : book.title,
        "author" : book.author,
        "year" : book.year,
        "isbn" : book.isbn,
        "review_count" : res['work_reviews_count'],
        "average_score" : res['average_rating']
    })
