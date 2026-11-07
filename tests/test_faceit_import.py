
from services.faceit_api import (
    get_player,
    get_player_matches,
    get_match_details
)

nickname = input("Введите FACEIT nickname: ")

player = get_player(nickname)

if not player:
    print("Игрок не найден!")
    exit()

matches = get_player_matches(player["player_id"], limit=1)

if not matches or not matches.get("items"):
    print("Матчи не найдены!")
    exit()

match_id = matches["items"][0]["match_id"]

print("\nMatch ID:", match_id)

details = get_match_details(match_id)

print("\n========== MATCH DETAILS ==========")

if details:
    print("Keys:", details.keys())
    print("\nПолные данные матча:")
    print(details)
else:
    print("Информация о матче не получена!")
