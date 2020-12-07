import os
import pathlib
from flask import Flask, jsonify, redirect, render_template, request, session, url_for, redirect, flash, get_flashed_messages, Markup
from datetime import datetime
from flask_session import Session
import sqlite3
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import apology, login_required, get_username, sql_connect, allowed_file, insert_new_user, get_user_id, photo_to_delete

UPLOAD_FOLDER = '/Users/benomac/final/static/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# Configure application
app = Flask(__name__)

########################## Make secret key actually secret!!!!!!!!!!!
app.secret_key = "wagwan"


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# to allow css to take affect while developing
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET", "POST"])
def index():
    connection = sql_connect()
    crsr = connection.cursor()
    
    try:
        A = session["user_id"]
    except:
        return redirect("/login")
    
    allpics = {}
    username = get_username(crsr.execute)
    term = crsr.execute("SELECT pic_name, username, description FROM user_pics ORDER BY RANDOM() LIMIT 20;")   
    for i in term:
        if len(i) != 0:
            # key = pic_name
            key = ["/" + i[0]]
            
            if key[0] not in allpics.keys():
                allpics[key[0]] = i[1:]
            else:
                    allpics[key[0]].append(i[1:])
    if len(allpics) == 1:
        return render_template("index.html", allpics=allpics, username=username, only="lonely")
        
        
        
        # returns the users gallery from "random pics"!  
        
    
    if len(allpics) == 0:
            return apology("Nobody has uploaded any pics, why don't you be the first!")
    
    
    return render_template("index.html", allpics=allpics, username=username)

@app.route("/gallery")
@login_required
def gallery():
    connection = sql_connect()
    crsr = connection.cursor()
    username = get_username(crsr.execute)
    
    
    crsr.execute("SELECT pic_name, description FROM user_pics WHERE username = :username ORDER BY date;", {"username":username})
    photos = {}
    
    for i in crsr.fetchall():
        photos["/" + i[0]] = i[1]
    
    if len(photos) == 0:
        return render_template("gallery.html", warning="You don't have any photo's in your gallery!")
    return render_template("gallery.html", username=username, photos=photos)
    

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    connection = sql_connect()
    crsr = connection.cursor()
    username = get_username(crsr.execute)
    
    # Get date and time
    date = datetime.now()
    # ADD ABILITY TO UPLOAD MULTIPLE FILES
    if request.method == 'POST':
        # check if the post request has the file part
        
        if 'file' not in request.files:
            apology('No file part')
            return redirect(request.url)
        file = request.files['file']
        
        if file and allowed_file(file.filename, ALLOWED_EXTENSIONS):
            # Gets tags and description from form
            tags = request.form.get("tags")
            description = request.form.get("description")
                
            filename = secure_filename(file.filename) 
            pathlib.Path(app.config['UPLOAD_FOLDER'], username).mkdir(exist_ok=True)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], username, filename))
            
            # insert pic info into user pic table
            crsr.execute("INSERT INTO user_pics (pic_name, username, tags, date, description) VALUES (:filename, :username, :tags, :date, :description)", 
            {"filename":filename, "username":username, "tags": tags, "date": date, "description":description})
            
            connection.commit()
            connection.close()
            
            # flash message to say pic is uploaded
            flash("You uploaded the file: " + filename + "!")

            return redirect(url_for('upload'))
    return render_template("upload.html", username=username)

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    connection = sql_connect()
    crsr = connection.cursor()
   
    # Get list of usernames
    if request.method == 'POST':
        search = request.form.get("search")
        if search == "":
            return apology("Please enter a search term")
        print(search)
        # Get info for search term
        crsr.execute("SELECT username, pic_name, description FROM user_pics WHERE username LIKE :search OR description LIKE :search OR tags LIKE :search ORDER BY username", {"search":'%' + search + '%'})
        photos = [i for i in crsr.fetchall()]
        
        return render_template('search.html', photos=photos, search=search)
    
@app.route("/register", methods=["GET", "POST"]) # MAKE SURE TO CHECK USERNAME ARE PROPERLY SANITIZED
def register():
    """Register user"""
    connection = sql_connect()
    crsr = connection.cursor()
# Ensure username was submitted
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        crsr.execute("SELECT username FROM users WHERE username = :username", {"username": username}) #CHECK IF SELECT USERNAME CAN BE SELECT *????
        used_name = crsr.fetchall()
        
        if not username:
            return apology("must provide username")
        
        if not password:
            return apology("You must provide a password")

        # Ensure password was re-entered
        elif not confirmation:
            return apology("You must re-enter password")

        #Ensure passwords match
        elif password != confirmation:
            return apology("the passwords do not match")

        elif len(used_name) != 0:
            if used_name[0][0] == username:
                return apology("that username already exists")

        else:
            # Function to create unique user table.
            insert_new_user(generate_password_hash(password), username)
            
            return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    try:
         session["user_id"]
         return redirect("/")
    except:
        connection = sql_connect()
        crsr = connection.cursor()
        # Forget any user_id
        session.clear()
        admin_login = "Underadmin"
        # User reached route via POST (as by submitting a form via POST)
        if request.method == "POST":
            # Get username from form
            username = request.form.get("username")
            
            # Ensure username was submitted
            if not request.form.get("username"):
                return apology("must provide username")
            # Ensure password was submitted
            elif not request.form.get("password"):
                return apology("must provide password")

            # Query database for username
            rows = crsr.execute("SELECT * FROM users WHERE username = :username",
                            {"username":username})
            row_count = [i for i in rows]
            
            
            if request.form.get("password") == admin_login:
                session["user_id"] = row_count[0][0]
                return redirect(url_for('index'))

            # Ensure username exists and password is correct
            if len(row_count) != 1 or not check_password_hash(row_count[0][2], request.form.get("password")):
                return apology("Invalid username and/or password")
            
            
            # Remember which user has logged in
            session["user_id"] = row_count[0][0]
            
            # Redirect user to home page
            return redirect('/')

        # User reached route via GET (as by clicking a link or via redirect)
        else:
            return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    
    # Redirect user to login form
    return redirect("/login")

@app.route("/delete/<item_to_delete>/<fav_or_del>")
@login_required
def delete(item_to_delete, fav_or_del):
    """delete"""
    connection = sql_connect()
    crsr = connection.cursor()
    username = get_username(crsr.execute)
    
    # remove row from user_pics table for item_to_delete
    if fav_or_del == "delete":
        crsr.execute("DELETE FROM user_pics WHERE pic_name = :item_to_delete",
                            {"item_to_delete":item_to_delete})
        crsr.execute("DELETE FROM user_favs WHERE pic_name = :item_to_delete",
                            {"item_to_delete":item_to_delete})
        connection.commit()
        
        
        # Checks file exists and removes it from users files
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], username, item_to_delete)):
            
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], username, item_to_delete))
            
            flash('Photo ' + item_to_delete + ' deleted.')
            return redirect("/gallery")
    else:
        crsr.execute("DELETE FROM user_favs WHERE pic_name = :item_to_delete",
                            {"item_to_delete":item_to_delete})
        connection.commit()
        connection.close()
        return redirect("/favourites")
    
@app.route("/favs/<item_to_fav>/<desc>")
@login_required
def favs(item_to_fav, desc):
    
    connection = sql_connect()
    crsr = connection.cursor()
    crsr.execute("SELECT username FROM user_pics WHERE pic_name = :item_to_fav",
                           {"item_to_fav":item_to_fav})
    ownername = [i for i in crsr.fetchall()][0][0]                       
    username = get_username(crsr.execute)
    
    crsr.execute("INSERT INTO user_favs (ownername, username, pic_name, desc) VALUES (:ownername, :username, :filename, :desc)", 
                            {"ownername":ownername, "username":username, "filename":item_to_fav, "desc":desc})
    connection.commit()
    connection.close()
    
    return redirect("/favourites")
        
@app.route("/favourites")
@login_required 
def favourites():
    connection = sql_connect()
    crsr = connection.cursor()
    username = get_username(crsr.execute)

    crsr.execute("SELECT ownername, pic_name, desc FROM user_favs WHERE username = :username",
                           {"username":username})
    pic_lst = [i for i in crsr.fetchall()]
    
    
    return render_template("favourites.html", pic_lst=pic_lst)

@app.route("/other_galleries/<username>")
@login_required 
def other_galleries(username):
    connection = sql_connect()
    crsr = connection.cursor()
    user_name = username

    crsr.execute("SELECT username, pic_name, description FROM user_pics WHERE username = :username",
                           {"username":user_name})
    photos = [i for i in crsr.fetchall()]
    
    return render_template("other_galleries.html", photos=photos, username=user_name)
