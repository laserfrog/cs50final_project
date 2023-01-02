from flask import Flask, render_template, request, session, redirect
from flask_session import Session
import json
import requests
import sys
from helpers import game_lookup
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from howlongtobeatpy import HowLongToBeat
import ast
app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True


# Session stuff
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# initilise the database
db = SQL("sqlite:///game.db")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        pass
    else:
        return render_template("index.html")


@app.route("/search")
def search():
    game_search = request.args.get("search")
    game_list = game_lookup(game_search)

    return render_template("searched.html", response=game_list)


@app.route("/register", methods=["GET", "POST"])
def register():
    """ Registers the user"""
    if request.method == "POST":
        if not request.form.get("username"):
            error = "Please provide a username"
            return render_template("error.html", error=error)
        elif not request.form.get("password"):
            error = "Please provide a password"
            return render_template("error.html", error=error)
        elif request.form.get("password") != request.form.get("confirmation"):
            error = "Passwords must match"
            return render_template("error.html", error=error)
        else:
            username = request.form.get("username")
            password = generate_password_hash(request.form.get("password"))
            username_check = db.execute(
                "SELECT * FROM user_login WHERE username = ?", username)
            if username_check:
                error = "There's already a user with that name"
                return render_template("error.html", error=error)
            else:
                db.execute(
                    "INSERT INTO user_login (username, hash) VALUES(?, ?)", username, password)
                return_string = f"Thanks {username}! You are now registered."
                return render_template("register.html", confirm=return_string)
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """ Logs the user in"""

    # Forget user id
    session.clear()

    if request.method == "POST":

        if not request.form.get("username"):
            error = "Must provide username"
            return render_template("error.html", error=error)

        elif not request.form.get("password"):
            error = "Must provide password"
            return render_template("error.html", error=error)

        rows = db.execute(
            "SELECT * FROM user_login WHERE username = ?", request.form.get("username"))

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            error = "Invalid username or password"
            return render_template("error.html", error=error)

        session["user_id"] = rows[0]["id"]

        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    "Log me out"

    session.clear()

    return redirect("/")


@app.route("/add_game", methods=["GET", "POST"])
def add_game():
    """ Looks at the game to be added."""

    if request.method == "POST":
        game = request.form.get("id")
        game = ast.literal_eval(game)
        game_name = game["name"]
        results = HowLongToBeat().search(game_name, similarity_case_sensitive=False)
        if results:
            results = results[0]
            results = results.main_story
            game["how_long"] = results
        else:
            results = None
        print(type(results), sys.stdout)

        return render_template("add_game.html", game=game, howlong=results)


@app.route("/game_added", methods=["GET", "POST"])
def game_added():
    """ Adss game to database."""
    if request.method == "POST":
        game = request.form.get("game")
        game = ast.literal_eval(game)

        platforms = request.form.getlist('mycheckbox')
        game["platforms"] = platforms

        return render_template("game_added.html", game=game, platforms=platforms)
