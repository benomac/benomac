import os
import requests
import urllib.parse
import sqlite3

# benstagram!

from flask import redirect, render_template, request, session
from functools import wraps

def apology(message):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        
    return render_template("apology.html", bottom=message)

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def get_username(a):
    username = a("SELECT username from users WHERE id=:id", {"id":session['user_id']})
    user = [i for i in username]
    return user[0][0]

def get_user_id(a):
    username = a("SELECT id from users WHERE id=:id", {"id":session['user_id']})
    user_id = [i for i in username]
    return user_id[0][0]

    
def allowed_file(filename, ALLOWED_EXTENSIONS):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sql_connect():
    # connecting to the database  
    connection = sqlite3.connect("gallery.db") 

    # connecting to the database  
    connection = sqlite3.connect("gallery.db") 
    return connection

def insert_new_user(hash_pw, username):
    connection = sql_connect()
    crsr = connection.cursor()
    # Create a password hash and insert user data into USERS    
    hashed = hash_pw
    crsr.execute("INSERT INTO users (username, hash) VALUES (:username, :hashed)", {"username": username, "hashed":hashed})
    
    #commit the insertion to the table
    connection.commit()
    connection.close()


photo_to_delete = []
    # sql_command = """CREATE TABLE IF NOT EXISTS user_pics (pic_id INTEGER PRIMARY KEY, 
    #                                                         pic_name VARCHAR(255), 
    #                                                         user_id INTEGER NOT NULL, 
    #                                                         tags VARCHAR(255), 
    #                                                         date VARCHAR(30)); """
    
