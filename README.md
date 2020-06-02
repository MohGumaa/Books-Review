# Project 1:(Books-Review)
**Web Programming with Python and JavaScript Course.**
***
> Create Responsive website. Users will be able to register for website and
then log in using their username and password. Once they login, they will be able to search for books and leave their reviews for individual books, and see the reviews made by other people, Also can get book details and reviews Programmatically via website API.

__How to run App:__
```
pip install -r requirements.txt
export FLASK_APP=application.py
export FLASK_DEBUG=1
export DATABASE_URL="your postgreSQL form heroku Credentials"    
```
---
## API access for book details and review:
`/api/<isbn>`
