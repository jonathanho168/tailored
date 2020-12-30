import os
import math

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from cs50 import SQL
from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure SQLite database
db = SQL("sqlite:///recommendations.db")

# Column names in an array so that later statistics can be facilitated
keywords = ["acting", "adulthood", "afterlife", "americandream", "army", "artificialintelligence", "beauty", "benevolence", "betrayal", "blackmail", "bullying", "business", "career", "chaebol", "childhood", "coffeeshop", "competition", "conglomerate", "conservative", "conspiracy", "corruption", "crime", "cutthroat", "cynicism", "death", "debt", "dedication", "depression", "developer", "divorce", "doctor", "entrepreneur", "family", "fashion", "finance", "financialinstability", "food", "friendship", "ghost", "glassceiling", "growth", "heaven/hell", "highschool", "history", "hospital", "identity", "industry", "infidelity", "inheritance", "international", "investigation", "investment", "kpop", "long-lost", "love", "magic", "make-up", "manipulation", "marriage", "maturity", "mentalillness", "military", "modeling", "moneylaundering", "murder", "music", "negotiation", "northkorea", "obligation", "perseverance", "police", "politics", "poverty", "power", "progressive", "psychology", "reunite", "revenge", "rivalry", "romance", "sabotage", "sacrifice", "secondleadsyndrome", "shopping", "socialgood", "socialhierarchy", "socialmedia", "software", "suicide", "supernatural", "support", "survival", "suspense", "technology", "trauma", "travelling", "underdog", "university", "wealth", "wholesome", "workplace", "workplacehierarchy", "youth"]
ratings = ["acting_overall", "male_leads", "female_leads", "supportingcast", "soundtrack", "no_plotholes", "characterdev", "backstories", "plotdepth", "ending", "pacing", "not_cliche", "believable", "overall"]

# Show recommendations
@app.route("/")
@login_required
def index():
    # select all dramas with existing ratings
    dramas = db.execute("SELECT * FROM dramaprofile")
    # select all dramas the user has rated before so that we do not recommend these
    viewed = db.execute("SELECT english FROM viewed WHERE username = :username", username=session["user"])
    # select the user's existing profile of dramas they've liked
    # make a user profile if none exists
    exists = db.execute("SELECT * FROM userprofile WHERE username = :username", username=session["user"])
    if not exists:
        db.execute("INSERT INTO userprofile (username) VALUES (:username)", username=session["user"])
    profile = db.execute("SELECT * FROM userprofile WHERE username = :username", username=session["user"])
    # clear the existing recommendations so that we can make new ones every time they come to the webpage
    db.execute("DELETE FROM recommend WHERE username = :username", username=session["user"])

    quality = db.execute("SELECT english FROM ratings WHERE overall >= 5")
    # select shows above average rating (5/10 in overall)



    for drama in dramas:
        difference = 0
        false = 0
        true = 0
        for view in viewed:
            if drama["english"] == view["english"]:
                false = 1
        for show in quality:
            if drama["english"] == show["english"]:
                true = 1

        if false == 0 and true == 1:
            for keyword in keywords:
                difference = drama[keyword] - profile[0][keyword]
                difference = difference ** 2
            db.execute("INSERT INTO recommend (username, english, score) VALUES (?, ?, ?)", session["user"], drama["english"], difference)

    recommended = db.execute("SELECT * FROM recommend JOIN dramas WHERE recommend.english = dramas.english AND username = :username ORDER BY score ASC LIMIT 30", username=session["user"])

    # set scores for all dramas
    # get top 10
    shownames = db.execute("SELECT * FROM ratings")
    for showname in shownames:
        score = 0
        for rating in ratings:
            score = score + showname[rating]
        score = score + math.sqrt(showname["overall"])
        db.execute("UPDATE ratings SET score = :score WHERE english = :english", score=score, english=showname["english"])

    top10 = db.execute("SELECT * FROM ratings JOIN dramas WHERE dramas.english = ratings.english ORDER BY score DESC LIMIT 10")

    name = db.execute("SELECT firstname FROM users WHERE username = :username", username=session["user"])
    firstname = name[0]["firstname"].capitalize()

    return render_template("index.html", recommended=recommended, top10=top10, firstname=firstname)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():

     # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure valid drama title was submitted
        drama = request.form.get("english")
        listdramas = db.execute("SELECT english FROM dramas")

        dramainlist = 0
        for item in listdramas:
            if item['english'] == drama:
                dramainlist = 1


        if dramainlist == 0:
            return apology("must provide valid english title", 403)

        # ensure user has not already added this show
        already = db.execute("SELECT * FROM viewed WHERE username = :username AND english = :english", username=session["user"], english=drama)
        if len(already) > 0:
            return apology("already added this show", 403)

        for keyword in keywords:
            dummy = 0
            # if the keyword does not apply
            if request.form.get(keyword):
                dummy = 1

            # update drama profile
            # make a drama profile if none exists
            exists = db.execute("SELECT english FROM dramaprofile WHERE english = :english", english=drama)
            if not exists:
                db.execute("INSERT INTO dramaprofile (english) VALUES (:drama)", drama=drama)

            current = db.execute("SELECT * FROM dramaprofile WHERE english = :english", english=drama)
            quantity = current[0]['quantity']
            value = current[0][keyword]
            value = (value * quantity) + dummy
            value = value / (quantity + 1)
            db.execute("UPDATE dramaprofile SET :keyword = :newvalue WHERE english = :english", keyword=keyword, newvalue=value, english=drama)

            # update user profile if user liked the drama
            if request.form.get("liked"):
                # make a user profile if none exists
                exists = db.execute("SELECT * FROM userprofile WHERE username = :username", username=session["user"])
                if not exists:
                    db.execute("INSERT INTO userprofile (username) VALUES (:username)", username=session["user"])

                current = db.execute("SELECT * FROM userprofile WHERE username = :username", username=session["user"])
                quantity = current[0]['quantity']
                value = current[0][keyword]
                value = (value * quantity) + dummy
                value = value / (quantity + 1)
                db.execute("UPDATE userprofile SET :keyword = :newvalue WHERE username = :username", keyword=keyword, newvalue=value, username=session["user"])

        if request.form.get("liked"):
            # add liked drama to userliked
            db.execute("INSERT INTO liked (username, english) VALUES (?, ?)", session["user"], drama)

        # add drama to viewed regardless of liked
        db.execute("INSERT INTO viewed (username, english) VALUES (?, ?)", session["user"], drama)

        # Update drama rating, for all categories including overall rating for the drama
        # BUT NOT THE SCORE WE USE FOR TOP 10
        for rating in ratings:
            if request.form.get(rating):

                # make a drama rating profile if none exists
                exists = db.execute("SELECT * FROM ratings WHERE english = :english", english=drama)
                if not exists:
                    db.execute("INSERT INTO ratings (english) VALUES (:english)", english=drama)

                current = db.execute("SELECT * FROM ratings WHERE english = :english", english=drama)
                quantity = current[0]['quantity']
                value = current[0][rating]
                value = (value * quantity) + dummy
                value = value / (quantity + 1)
                db.execute("UPDATE ratings SET :rating = :newvalue WHERE english = :english", rating=rating, newvalue=value, english=drama)



        # Increment count of list size for user's profile and drama's profile
        db.execute("UPDATE userprofile SET quantity = quantity + 1 WHERE username = :username", username=session["user"])
        db.execute("UPDATE dramaprofile SET quantity = quantity + 1 WHERE english = :drama", drama=drama)
        db.execute("UPDATE ratings SET quantity = quantity + 1 WHERE english = :drama", drama=drama)

        return redirect("/")

    else:
        # if request method is GET
        return render_template("add.html", ratings=ratings, keywords=keywords)

# Log user in
@app.route("/login", methods=["GET", "POST"])
def login():
        # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["user"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

# Log user out
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# Register a new user
@app.route("/register", methods=["GET", "POST"])
def register():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure first name was submitted
        elif not request.form.get("firstname"):
            return apology("must provide first name", 403)

        # Ensure password was submitted
        elif not request.form.get("lastname"):
            return apology("must provide last name", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password was retyped
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 403)

        # Ensure password was confirmed
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # Ensure unique username
        if len(rows) == 1:
            return apology("choose another username", 403)

        # Store name, unique username and hashed password in finance.db
        db.execute("INSERT INTO users (username, hash, firstname, lastname) VALUES (?, ?, ?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")), request.form.get("firstname"), request.form.get("lastname"))

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)