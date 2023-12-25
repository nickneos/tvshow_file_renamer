import requests
import json
import os
from urllib.parse import quote
from pathlib import Path

URL = "https://api4.thetvdb.com/v4"
HOME_DIR = Path(__file__).resolve(strict=True).parents[1]
API_FILE = os.path.join(HOME_DIR, "api_key.txt")
TOKEN_JSON = os.path.join(HOME_DIR, "token.json")
CACHE = os.path.join(HOME_DIR, "cache/")


def generate_token(api_key_file=API_FILE):
    with open(api_key_file, mode="r") as f:
        api_key = f.read().strip()

    endpoint = "/login"
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    data = {"apikey": api_key}

    response = requests.post(URL + endpoint, headers=headers, json=data)

    if response.status_code == 200:
        with open(TOKEN_JSON, "w") as f:
            json.dump(response.json(), f, indent=2)
        return True
    return False


def read_token_from_file(json_file=TOKEN_JSON):
    try:
        with open(json_file) as f:
            j = json.load(f)
        return j["data"]["token"]
    except FileNotFoundError:
        generate_token()
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


def find_series(search_string, type="series", **kwargs):
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
        data = response["data"][0]
        return data
    except (KeyError, IndexError, TypeError):
        return None


def get_series_data(series_id):
    # TODO: if active show, query api if cached file is older than a week
    if Path(os.path.join(CACHE, f"{series_id}.json")).exists():
        with open(os.path.join(CACHE, f"{series_id}.json"), "r") as f:
            data = json.load(f)
    # otherwise query api
    else:
        endpoint = f"/series/{series_id}/episodes/default/eng?page=0"
        data = tvdb_request(URL + endpoint)
        # save to cache
        with open(os.path.join(CACHE, f"{series_id}.json"), "w") as f:
            json.dump(data, f, indent=2)

    return data


def get_episode_details(series_id, season_num, episode_num):
    json_data = get_series_data(series_id)

    for episode in json_data["data"]["episodes"]:
        if episode["seasonNumber"] == season_num:
            if episode["number"] == episode_num:
                return episode


def get_series_details(series_id):
    return get_series_data(series_id)["data"]


read_token_from_file()

if not Path(CACHE).exists():
    os.mkdir(CACHE)


if __name__ == "__main__":
    j = find_series("mr robot", kwargs={"year": 2015})
    print(json.dumps(j, indent=2))
