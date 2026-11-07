
from datetime import datetime

from services.faceit_api import (
    get_player,
    get_player_matches as get_faceit_matches,
    get_match_details
)

from services.database import save_player
from services.faceit_demo_download import download_faceit_demo
from services.leetify_import import import_matches

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

    # 3. Сохранение игрока в PostgreSQL
    player_db_id = save_player(player)

    player_id = player["player_id"]
    player_steam_id = player["games"]["cs2"]["game_player_id"]

    print("Player database ID:", player_db_id)

    # 4. Информация об игроке
    print("\n===== PLAYER INFORMATION =====")

    print("Nickname:", player["nickname"])
    print("ELO:", player["games"]["cs2"]["faceit_elo"])
    print("Steam ID:", player_steam_id)

    # 5. Импорт матчей Leetify
    print("\n===== LEETIFY DATA IMPORT =====")

    imported_steam_id = import_matches(nickname)

    if not imported_steam_id:
        print("Не удалось загрузить статистику Leetify!")
        return

    # 6. Общая статистика
    stats = get_overall_stats(imported_steam_id)

    print("\n===== OVERALL STATISTICS =====")

    for name, value in stats.items():
        print(f"{name}: {value}")

    # 7. Победы и поражения
    win_stats = get_win_stats(imported_steam_id)

    print("\n===== WIN / LOSS STATISTICS =====")

    print("Completed matches:", win_stats["completed_matches"])
    print("Wins:", win_stats["wins"])
    print("Losses:", win_stats["losses"])
    print("Win Rate:", str(win_stats["win_rate"]) + "%")

    # 8. Статистика по картам
    maps = get_map_stats(imported_steam_id)

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

    # 9. Последние 10 матчей
    recent_matches = get_recent_matches(imported_steam_id, 10)

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

    # 10. Получение истории матчей FACEIT
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

    # 11. Вывод списка матчей
    print("\n===== MATCH LIST =====")

    available_matches = []

    for match in matches:

        teams = match.get("teams", {})
        my_team = None

        for team_name, team_data in teams.items():

            for match_player in team_data.get("players", []):

                if match_player["player_id"] == player_id:
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

        match_date = datetime.fromtimestamp(
            match["started_at"]
        ).strftime("%d.%m.%Y %H:%M")

        opponent_name = teams.get(opponent_team, {}).get(
            "nickname", "Unknown"
        )

        available_matches.append(match)

        print(f"\n{len(available_matches)}. {match_date}")
        print("Opponent:", opponent_name)
        print("Score:", f"{my_score} : {opponent_score}")
        print("Result:", result)
        print("Match ID:", match["match_id"])

    if not available_matches:
        print("Нет доступных матчей для выбора!")
        return

    # 12. Выбор матча
    print("\n===== SELECT MATCH =====")

    match_number_text = input(
        f"Enter match number (1-{len(available_matches)}): "
    )

    try:
        match_number = int(match_number_text)
    except ValueError:
        print("Введите корректный номер!")
        return

    if match_number < 1 or match_number > len(available_matches):
        print("Invalid match number!")
        return

    selected_match = available_matches[match_number - 1]
    selected_match_id = selected_match["match_id"]

    print("\n===== SELECTED MATCH =====")
    print("Match ID:", selected_match_id)

    # 13. Получение подробной информации о матче
    print("\n===== MATCH DETAILS =====")

    match_details = get_match_details(selected_match_id)

    if not match_details:
        print("Не удалось получить информацию о матче!")

    else:

        demo_urls = match_details.get("demo_url", [])

        if not demo_urls:
            print("Для этого матча демо недоступно!")

        else:

            demo_url = demo_urls[0]

            print("\n===== AUTOMATIC DEMO DOWNLOAD =====")

            try:

                demo_path = download_faceit_demo(
                    selected_match_id,
                    demo_url
                )

                if demo_path:
                    print("\nDemo saved:", demo_path)
                else:
                    print("Не удалось скачать демо.")

            except Exception as error:

                print("\nОшибка скачивания демо!")
                print("Причина:", error)
                print("Попробуй скачать демо позже.")

    print("\n===== COMPLETED =====")


if __name__ == "__main__":
    main()
