import requests
from config.settings import FACEIT_API_KEY

BASE_URL = "https://open.faceit.com/data/v4"

headers = {
    "Authorization": f"Bearer {FACEIT_API_KEY}",
    "Accept": "application/json"
}


def get_player(nickname):
    url = f"{BASE_URL}/players"

    params = {
        "nickname": nickname,
        "game": "cs2"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.status_code)
        return None

def get_player_matches(player_id, limit=20):
    url = f"{BASE_URL}/players/{player_id}/history"

    params = {
        "game": "cs2",
        "limit": limit
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()

    print("Error:", response.status_code)
    return None

def get_match_stats(match_id):
    url = f"{BASE_URL}/matches/{match_id}/stats"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()

    print("Error:", response.status_code)
    return None
def get_my_stats(match_stats, player_id):

    for round_data in match_stats["rounds"]:

        for team in round_data["teams"]:

            for player in team["players"]:

                if player["player_id"] == player_id:

                    return player["player_stats"]

    return None


def get_match_details(match_id):
    url = f"{BASE_URL}/matches/{match_id}"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()

    print("Match details error:", response.status_code)
    return None

def get_match_details(match_id):
    url = f"{BASE_URL}/matches/{match_id}"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()

    print("Match details error:", response.status_code)
    print(response.text)
    return None