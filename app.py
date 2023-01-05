from flask import Flask, render_template, request, session, redirect, flash
from flask_session import Session
import json
import requests
import sys
from helpers import game_lookup
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from howlongtobeatpy import HowLongToBeat
import ast
from datetime import date
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
            results = 0
            game["how_long"] = results
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

        platformsstring = ''
        for x in platforms:
            platformsstring += '_' + x
        platformsstring += '_'
        if not session.get("user_id"):
            return redirect("/login")
        user_id = session.get("user_id")
        db.execute(
            "INSERT INTO game_database (user_id, game_name, box_art, deck, release_date, platforms, url, how_long) VALUES(?, ?, ? ,?, ?, ?, ?, ?)", user_id, game["name"], game["box_art"], game["deck"], game["release_date"], platformsstring, game["api_detail_url"], game["how_long"])
        flash("Game added!")
        return redirect("/game_database")


@app.route("/game_database", methods=["GET", "POST"])
def game_database():
    """Shows your database of games."""
    current_year = date.today().year
    assend = ["ASC", "DESC"]
    if request.method == "POST":
        asc = request.form.get('ascend')
        platform = request.form.get('platform')
        year = request.form.get('year')
        if asc not in assend:
            error = "SQL injection"
            return render_template("error.html", error=error)
        elif platform and year:
            platform = '%' + platform + '%'
            rows = db.execute(
                f"SELECT * FROM game_database WHERE user_id = ? AND platforms LIKE ? AND strftime('%Y', release_date) = ? ORDER BY game_name {asc}", session.get("user_id"), platform, year)
        elif platform:
            platform = '%' + platform + '%'
            rows = db.execute(
                f"SELECT * FROM game_database WHERE user_id = ? AND platforms LIKE ? ORDER BY game_name {asc}", session.get("user_id"), platform)
        elif year:
            rows = db.execute(
                f"SELECT * FROM game_database WHERE user_id = ? AND strftime('%Y', release_date) = ? ORDER BY game_name {asc}", session.get("user_id"), year)
        else:
            rows = db.execute(
                f"SELECT * FROM game_database WHERE user_id = ? ORDER BY game_name {asc}", session.get("user_id"))
            print(
                f"It IS {asc} the platform {platform} and year {year}", sys.stdout)
        return render_template("game_database.html", rows=rows, year=current_year, assend=assend)
    else:
        rows = db.execute(
            "SELECT * FROM game_database WHERE user_id = ?", session.get("user_id"))
        return render_template("game_database.html", rows=rows, year=current_year, assend=assend)


@app.route("/game_info", methods=["GET", "POST"])
def game_info():
    """Shows info on your game and lets to delete it from the database."""
    if request.method == "POST":
        game_id = request.form.get('id')
        game = ast.literal_eval(game_id)
        return render_template("game_info.html", game=game)


@app.route("/game_removed", methods=["GET", "POST"])
def game_removed():
    """Removes game from database."""
    if request.method == "POST":
        id = request.form.get('game')
        print(id, sys.stdout)
        db.execute("DELETE FROM game_database WHERE id = ?", id)
        flash("Game removed.")
        return redirect("/game_database")
