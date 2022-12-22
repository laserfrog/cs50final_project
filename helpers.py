import os
import requests
import urllib.parse
import json

from flask import redirect, render_template, request, session
from functools import wraps


def game_lookup(name):
    api_key = '5be92d215b6f9f44e4a1bba1f24ff25f42a0813c'
    url = f'http://www.giantbomb.com/api/search/?api_key={api_key}&format=json&query="{name}"&resources=game'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0'}
    response = requests.get(url, headers=headers)
    json_data = response.json()
    formatted_json = json.dumps(json_data, indent=4)
    results = json.loads(formatted_json)
    results = results["results"]
    game_list = []
    for i in range(len(results)):

        id = i

        result_loop = results[i]
        game_name = result_loop["name"]
        box_art = result_loop["image"]
        platforms = result_loop["platforms"]

        platform_list = []
        try:
            for n in range(len(platforms)):
                platform = platforms[n]
                platform_list.append(platform["name"])
        except TypeError:
            pass

        game_dict = {
            "id": id,
            "name": game_name,
            "box_art": box_art["thumb_url"],
            "deck": result_loop["deck"],
            "release_date": result_loop["original_release_date"],
            "platforms": platform_list,
            "api_detail_url": result_loop["api_detail_url"]
        }
        game_list.append(game_dict)
    return game_list
