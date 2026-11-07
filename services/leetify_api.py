import os
import requests
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BASE_URL = "https://api-public.cs-prod.leetify.com"
API_KEY = os.getenv("LEETIFY_API_KEY")


def validate_api_key():
    if not API_KEY:
        print("API key not found in .env!")
        return False

    url = f"{BASE_URL}/api-key/validate"

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    response = requests.get(url, headers=headers)

    print("Status code:", response.status_code)
    print("Response:", response.text[:500])

    return response.status_code == 200


def get_player_matches(steam_id):
    url = f"{BASE_URL}/v3/profile/matches"

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    params = {
        "steam64_id": steam_id
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    response.raise_for_status()

    return response.json()

if __name__ == "__main__":
    steam_id = "76561198399750074"

    try:
        matches = get_player_matches(steam_id)

        print("SUCCESS!")
        print("Matches found:", len(matches))

        if matches:
            print("First match:")
            print(matches[0])

    except requests.HTTPError as error:
        print("HTTP ERROR:", error.response.status_code)
        print("Response:", error.response.text[:500])