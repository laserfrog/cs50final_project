from flask import Flask, render_template, request
import json
import requests
import sys
from helpers import game_lookup

app = Flask(__name__)


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
