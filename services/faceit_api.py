
import requests
from config.settings import FACEIT_API_KEY

BASE_URL = "https://open.faceit.com/data/v4"

headers = {
    "Authorization": f"Bearer {FACEIT_API_KEY}",
    "Accept": "application/json"
}


def make_request(url, params=None):
    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()

        print("FACEIT API Error:", response.status_code)
        print(response.text[:500])

        return None

    except requests.RequestException as error:
        print("Request error:", error)
        return None


def get_player(nickname):
    url = f"{BASE_URL}/players"

    params = {
        "nickname": nickname,
        "game": "cs2"
    }

    return make_request(url, params)


def get_player_matches(player_id, limit=20):
    url = f"{BASE_URL}/players/{player_id}/history"

    params = {
        "game": "cs2",
        "limit": limit
    }

    return make_request(url, params)


def get_match_stats(match_id):
    url = f"{BASE_URL}/matches/{match_id}/stats"

    return make_request(url)


def get_match_details(match_id):
    url = f"{BASE_URL}/matches/{match_id}"

    return make_request(url)


def get_my_stats(match_stats, player_id):
    if not match_stats:
        return None

    for round_data in match_stats.get("rounds", []):
        for team in round_data.get("teams", []):
            for player in team.get("players", []):

                if player.get("player_id") == player_id:
                    return player.get("player_stats")

    return None
