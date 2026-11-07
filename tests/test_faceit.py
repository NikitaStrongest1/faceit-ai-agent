
from services.faceit_api import get_player, get_player_matches

nickname = input("Введите FACEIT nickname: ")

player = get_player(nickname)

if player:
    print("\nPlayer:", player.get("nickname"))
    print("Player ID:", player.get("player_id"))

    matches = get_player_matches(player["player_id"])

    if matches:
        match_list = matches.get("items", [])

        print("\nMatches found:", len(match_list))

        for match in match_list[:5]:
            print(
                match.get("match_id"),
                match.get("game_mode"),
                match.get("started_at")
            )
    else:
        print("Matches not found.")
else:
    print("Player not found.")
