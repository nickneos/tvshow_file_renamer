import requests
import json
import os
from urllib.parse import quote
from pathlib import Path

URL = "https://api4.thetvdb.com/v4"
API_KEY = "19f970d5-e640-4401-82c2-2cc42d125b0f"


def generate_token(api_key=API_KEY):
    endpoint = "/login"
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    data = {"apikey": api_key}

    response = requests.post(URL + endpoint, headers=headers, json=data)

    if response.status_code == 200:
        with open("token.json", "w") as f:
            json.dump(response.json(), f, indent=2)
        return True
    return False


def read_token_from_file(json_file="token.json"):
    try:
        with open(json_file) as f:
            j = json.load(f)
        return j["data"]["token"]
    except FileNotFoundError:
        generate_token(API_KEY)
        read_token_from_file()


def tvdb_request(api_url, retries=1):
    while retries > 0:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {read_token_from_file()}",
        }
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:  # unauthorized
            generate_token()
        retries -= 1

    return None


def get_show_id(search_string, type="series", **kwargs):
    """
    Returns the TVDB ID for a query.

    Args:
        search_string (str): The primary search string
        type (str): Can be movie, series, person, or company.
                    (default="series")
        **kwargs: Additional keyword arguments to add to search
                    string.

    Returns:
        id: TVDB ID
    """
    # first try getting from cache
    if not Path("cache/").exists():
        os.mkdir("cache/")

    for file in os.listdir("cache/"):
        if file.endswith(".json"):
            with open("cache/" + file, "r") as f:
                data = json.load(f)["data"]
            if data["name"].lower() == search_string.strip().lower():
                return (
                    data["id"],
                    data["name"],
                    data["year"],
                )

    # use api when not found in cache
    q = quote(search_string)
    endpoint = f"/search?query={q}&type={type}"

    for key, value in kwargs.items():
        endpoint += f"&{key}={quote(str(value))}"
    response = tvdb_request(URL + endpoint)

    try:
        return (
            response["data"][0]["tvdb_id"],
            response["data"][0]["name"],
            response["data"][0]["year"],
        )
    except (KeyError, IndexError):
        return None


def get_episodes(series_id):
    # first try retreving from cache
    # TODO: if active show, query api if cached file is older than a week
    if Path(f"cache/{series_id}.json").exists():
        with open(f"cache/{series_id}.json", "r") as f:
            episodes = json.load(f)
    # otherwise query api
    else:
        endpoint = f"/series/{series_id}/episodes/default/eng?page=0"
        episodes = tvdb_request(URL + endpoint)
        # save to cache
        with open(f"cache/{series_id}.json", "w") as f:
            json.dump(episodes, f, indent=2)

    return episodes


def get_episode_details(series_id, season_num, episode_num):
    json_data = get_episodes(series_id)

    for episode in json_data["data"]["episodes"]:
        if episode["seasonNumber"] == season_num:
            if episode["number"] == episode_num:
                return (episode["aired"], episode["name"], episode["overview"])


if __name__ == "__main__":
    # print(get_show_id("Alias"))
    # # json_data = get_episodes(id)
    # x = get_episode_details(75299, 1, 3)
    # print(x)
    generate_token(api_key=API_KEY)
