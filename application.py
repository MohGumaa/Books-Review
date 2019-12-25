import os, requests

from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from werkzeug.security import check_password_hash, generate_password_hash
from helper import login_required

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Index
@app.route("/")
def index():
    return render_template('index.html')

#  WTF registeration
class RegisterForm(Form):
    name = StringField('Name', validators=[validators.DataRequired(), validators.Length(min=4, max=25)])
    username = StringField('Username',validators= [validators.DataRequired(), validators.Length(min=4, max=25)])
    email = StringField('Email Address', validators=[validators.DataRequired(), validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')

# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
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

        #  Execute query  by insert into DB
        db.execute("INSERT INTO users (name, email, username, password) VALUES (:name, :email, :username, :password)",
                {"name": name, "email": email, "username": username, "password": password})

        # Commit to DB
        db.commit()

        # Close the DB
        db.close()

        # Flashing after complete transaction
        flash ('You are now registered and can log in', 'success')

        # Redirector
        return redirect(url_for('login'))

    return render_template('register.html', form = form)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():

    # Check if user access method
    if request.method == 'POST':

        # Get user data from Form
        username = request.form['username'].lower()
        password_enter = request.form['password']

        # Get username and password form database
        user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()

        # Ensure username exists and password is correct
        if user != None:
            password = user.password
            if check_password_hash(password, password_enter):
                session['logged_in'] = True
                session['username'] = username.capitalize()
                session["user_id"] = user.id

                message = f" Your are now logged in {session['username']}"
                flash(message, 'success')
                return redirect(url_for('index'))

            else:
                error = 'Invalid lgoin'
                return render_template('login.html', error=error)

                # CLose DB
                db.close()

        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Search route
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    """ Get book details """

    # Check if user access method
    if request.method == 'POST':

        # Check book isbn or title or author was provided
        if not request.form.get("book"):
            error = "you must provide abook details for search"
            return  render_template("dashboard.html", error=error)

        # Store query wildcard
        query = "%"+request.form.get("book")+"%"

        # Query DB for any match
        books_res = db.execute("SELECT * FROM books WHERE isbn LIKE :query OR title LIKE :query OR author LIKE :query",
                                {"query": query}).fetchall()

        # If nothing found
        if len(books_res) == 0:
            error = "We can't find any match. Try agin"
            return render_template("dashboard.html", error=error)

        # Retrun all matches
        msg = "book Found"
        return render_template('bookshow.html', books_res=books_res ,msg=msg)

    else:
        return render_template("search.html")

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
            flash('You already submitted a review for this book', 'warning')
            return redirect("/bookpage/" + isbn)
        else:
            db.execute("INSERT INTO reviews (review, rating, user_id, book_isbn) VALUES (:review, :rating, :user_id, :book_isbn)",
            {"review": review,
            "rating": rating,
            "user_id": session["user_id"],
            "book_isbn": isbn})

            db.commit()

            flash(' Review submit for this book', 'success')
            return redirect("/bookpage/" + isbn)


    # User access the page through GET
    else:
        # Query DB for any match
        book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                                {"isbn": isbn}).fetchone()

        """GoodReads API"""
        res = requests.get("https://www.goodreads.com/book/review_counts.json",
                           params={"key": "xC8CXDYwBlxBLMxmOHjyJw", "isbns": isbn}).json()["books"][0]

        ratings_count = res['work_ratings_count']
        average_rating = res['average_rating']

        reviews = db.execute("SELECT username, review, rating, publish_date FROM users INNER JOIN reviews ON users.id = reviews.user_id WHERE book_isbn = :isbn",{"isbn": isbn}).fetchall()

        print(reviews)

        return render_template('bookpage.html', book=book, ratings_count=ratings_count , average_rating=average_rating , reviews=reviews)

# Api route for get informatioon about any book
@app.route('/api/<string:isbn>')
def book_api(isbn):

    # Query DB for any match
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

    # Make sure book exists
    if book is None:
        return jsonify({"error": "Invalid book_isbn"}), 404

    """GoodReads API"""
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "xC8CXDYwBlxBLMxmOHjyJw", "isbns": isbn}).json()["books"][0]

    return jsonify({
            "isbn" : book.isbn,
            "title" : book.title,
            "author" : book.author,
            "year" : book.year,
            "ratings_count" : res['work_ratings_count'],
            "average_rating" : res['average_rating']
    })
