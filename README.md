# Project 1:(Books-Review)
**Web Programming with Python and JavaScript Course.**
***
> Create Responsive website. Users will be able to register for website and
then log in using their username and password. Once they login, they will be able to search for books and leave their reviews for individual books, and see the reviews made by other people, Also can get book details and reviews Programmatically via website API. In project their are two and main folder and one file:
1. static:
    *  __style.css__ : for design site structure.
    * __main.js__ : create XML request search for books and show in pages if exist or show error message if not.
2. templates:
    * __index__ : landing page for site.
    * __login__ : login page for site with username and password.
    * __register__ : Registration form for new user with required fields.
    * __dashboard__ : page for search for book by name or title or isbn.
    * __bookpage__ :  page for book details reviews by other people also  to write your review and rating ,access API.
3. application:
    * Handling registration request, logging in and logout, Also search for book and review and API access request.
    
---

__How to run App:__
```
pip install -r requirements.txt
export FLASK_APP=application.py
export FLASK_DEBUG=1
export DATABASE_URL="your postgreSQL form heroku Credentials"    
```
