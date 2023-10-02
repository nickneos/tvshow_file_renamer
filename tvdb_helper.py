import requests
import json
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
    with open(json_file) as f:
        j = json.load(f)
    return j["data"]["token"]


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
    q = quote(search_string)
    endpoint = f"/search?query={q}&type={type}"

    for key, value in kwargs.items():
        endpoint += f"&{key}={quote(str(value))}"
    response = tvdb_request(URL + endpoint)

    try:
        id = response["data"][0]["tvdb_id"]
    except (KeyError, IndexError):
        return None
    return id


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


if __name__ == "__main__":
    id = get_show_id("The Sopranos")
    json_data = get_episodes(id)
