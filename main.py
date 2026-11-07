
from services.faceit_api import (
    get_player,
    get_player_matches as get_faceit_matches
)

from services.faceit_import import import_matches

from services.analytics import (
    get_overall_stats,
    get_map_stats,
    get_win_stats,
    get_recent_matches
)


def main():

    print("\n===== FACEIT CS2 ANALYTICS =====")

    # 1. Ввод FACEIT ника
    nickname = input("\nEnter FACEIT nickname: ").strip()

    if not nickname:
        print("Nickname cannot be empty!")
        return

    # 2. Получение информации об игроке
    player = get_player(nickname)

    if not player:
        print("Player not found!")
        return

    player_id = player["player_id"]
    player_steam_id = player["games"]["cs2"]["game_player_id"]

    # 3. Информация об игроке
    print("\n===== PLAYER INFORMATION =====")

    print("Nickname:", player["nickname"])
    print("ELO:", player["games"]["cs2"]["faceit_elo"])
    print("Steam ID:", player_steam_id)

    # 4. Импорт матчей FACEIT в PostgreSQL
    print("\n===== FACEIT DATA IMPORT =====")

    player_db_id = import_matches(nickname)

    if not player_db_id:
        print("Не удалось загрузить статистику FACEIT!")
        return

    print("Player database ID:", player_db_id)

    # 5. Общая статистика
    stats = get_overall_stats(player_db_id)

    print("\n===== OVERALL STATISTICS =====")

    for name, value in stats.items():
        print(f"{name}: {value}")

    # 6. Победы и поражения
    win_stats = get_win_stats(player_db_id)

    print("\n===== WIN / LOSS STATISTICS =====")

    print("Completed matches:", win_stats["completed_matches"])
    print("Wins:", win_stats["wins"])
    print("Losses:", win_stats["losses"])
    print("Win Rate:", str(win_stats["win_rate"]) + "%")

    # 7. Статистика по картам
    maps = get_map_stats(player_db_id)

    print("\n===== MAP STATISTICS =====")

    print(
        f"{'MAP':<15}"
        f"{'MATCHES':<12}"
        f"{'AVG K/D':<12}"
        f"{'AVG ADR':<12}"
        f"{'AVG HS%':<12}"
    )

    print("-" * 63)

    for row in maps:

        map_name, matches, kills, deaths, kd, adr, hs = row

        print(
            f"{map_name:<15}"
            f"{matches:<12}"
            f"{kd:<12}"
            f"{adr:<12}"
            f"{hs:<12}"
        )

    # 8. Последние 10 матчей
    recent_matches = get_recent_matches(player_db_id, 10)

    print("\n===== LAST 10 MATCHES =====")

    print(
        f"{'MAP':<13}"
        f"{'SCORE':<10}"
        f"{'RESULT':<10}"
        f"{'K':<5}"
        f"{'D':<5}"
        f"{'A':<5}"
        f"{'K/D':<8}"
        f"{'ADR':<8}"
        f"{'HS%':<8}"
    )

    print("-" * 77)

    for row in recent_matches:

        (
            map_name,
            finished_at,
            player_score,
            opponent_score,
            match_result,
            kills,
            deaths,
            assists,
            kd,
            adr,
            hs_percent
        ) = row

        score = (
            f"{player_score}:{opponent_score}"
            if player_score is not None and opponent_score is not None
            else "N/A"
        )

        print(
            f"{str(map_name):<13}"
            f"{score:<10}"
            f"{match_result:<10}"
            f"{kills:<5}"
            f"{deaths:<5}"
            f"{assists:<5}"
            f"{str(kd):<8}"
            f"{str(adr):<8}"
            f"{str(hs_percent):<8}"
        )

    # 9. История матчей FACEIT
    print("\n===== FACEIT MATCH HISTORY =====")

    matches_data = get_faceit_matches(player_id, limit=20)

    if not matches_data:
        print("Не удалось получить матчи!")
        return

    matches = matches_data.get("items", [])

    print("Found matches:", len(matches))

    if not matches:
        print("Матчи не найдены!")
        return

    print("\n===== MATCH LIST =====")

    for index, match in enumerate(matches, start=1):

        teams = match.get("teams", {})
        my_team = None

        for team_name, team_data in teams.items():

            for match_player in team_data.get("players", []):

                if match_player.get("player_id") == player_id:
                    my_team = team_name
                    break

            if my_team:
                break

        if not my_team:
            continue

        opponent_team = (
            "faction1" if my_team == "faction2" else "faction2"
        )

        score = match.get("results", {}).get("score", {})

        my_score = score.get(my_team)
        opponent_score = score.get(opponent_team)

        if my_score is None or opponent_score is None:
            continue

        if match.get("results", {}).get("winner") == my_team:
            result = "WIN"
        else:
            result = "LOSS"

        opponent_name = teams.get(opponent_team, {}).get(
            "name", "Unknown"
        )

        print(f"\n{index}.")
        print("Opponent:", opponent_name)
        print("Score:", f"{my_score} : {opponent_score}")
        print("Result:", result)
        print("Match ID:", match["match_id"])

    print("\n===== COMPLETED =====")


if __name__ == "__main__":
    main()
