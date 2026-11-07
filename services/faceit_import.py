
from datetime import datetime, timezone

from services.faceit_api import (
    get_player,
    get_player_matches,
    get_match_stats,
    get_match_details
)

from services.database import get_connection, save_player


def to_int(value):
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def to_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def convert_timestamp(value):
    if value is None:
        return None

    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)

        if isinstance(value, str):
            try:
                timestamp = float(value)
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)
            except ValueError:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))

    except (ValueError, TypeError, OverflowError):
        return None

    return None


def import_matches(nickname):

    print("\nПолучаем профиль FACEIT...")

    player = get_player(nickname)

    if not player:
        print("Игрок не найден!")
        return None

    player_id = player.get("player_id")

    if not player_id:
        print("FACEIT Player ID не найден!")
        return None

    player_db_id = save_player(player)

    print("Игрок:", player.get("nickname"))
    print("FACEIT ID:", player_id)
    print("ID в PostgreSQL:", player_db_id)

    print("\nПолучаем историю матчей...")

    matches_data = get_player_matches(player_id, limit=20)

    if not matches_data:
        print("История матчей не найдена!")
        return None

    matches = matches_data.get("items", [])

    print("Найдено матчей:", len(matches))

    imported = 0
    skipped = 0

    with get_connection() as connection:

        for match in matches:

            match_id = match.get("match_id")

            if not match_id:
                skipped += 1
                continue

            print("\nОбрабатываем матч:", match_id)

            match_stats = get_match_stats(match_id)

            if not match_stats:
                print("Статистика матча недоступна!")
                skipped += 1
                continue

            rounds = match_stats.get("rounds", [])

            if not rounds:
                print("Данные матча отсутствуют!")
                skipped += 1
                continue

            teams = rounds[0].get("teams", [])

            details = get_match_details(match_id)

            if not details:
                print("Подробная информация о матче недоступна!")
                skipped += 1
                continue

            # Получаем карту
            voting = details.get("voting", {})
            map_data = voting.get("map", {})
            map_pick = map_data.get("pick")

            if isinstance(map_pick, list):
                map_name = map_pick[0] if map_pick else None
            else:
                map_name = map_pick

            # Получаем результаты матча
            results = details.get("results", {})
            faction_scores = results.get("score", {})
            winning_faction = results.get("winner")

            factions = details.get("teams", {})

            faction1_id = factions.get("faction1", {}).get("faction_id")
            faction2_id = factions.get("faction2", {}).get("faction_id")

            team1_score = to_int(faction_scores.get("faction1"))
            team2_score = to_int(faction_scores.get("faction2"))

            winner = None
            player_stats = None
            player_team_number = None

            # Обрабатываем ОБЕ команды
            for team_index, team in enumerate(teams, start=1):

                team_id = team.get("team_id")

                if team_id == faction1_id and winning_faction == "faction1":
                    winner = str(team_index)

                elif team_id == faction2_id and winning_faction == "faction2":
                    winner = str(team_index)

                # Ищем игрока, но не прерываем цикл
                for current_player in team.get("players", []):

                    if current_player.get("player_id") == player_id:

                        player_stats = current_player.get(
                            "player_stats", {}
                        )

                        player_team_number = team_index

            if not player_stats:
                print("Статистика игрока не найдена!")
                skipped += 1
                continue

            # Статистика игрока
            kills = to_int(player_stats.get("Kills"))
            deaths = to_int(player_stats.get("Deaths"))
            assists = to_int(player_stats.get("Assists"))

            kd = to_float(player_stats.get("K/D Ratio"))
            adr = to_float(player_stats.get("ADR"))

            hs_kills = to_int(player_stats.get("Headshots"))
            hs_percent = to_float(player_stats.get("Headshots %"))

            damage = to_int(player_stats.get("Damage"))
            trade_kills = to_int(player_stats.get("Trade Kills"))

            finished_at = convert_timestamp(
                details.get("finished_at")
            )

            # Сохраняем матч
            result = connection.execute(
                """
                INSERT INTO matches (
                    faceit_match_id,
                    map_name,
                    finished_at,
                    rounds_played,
                    team1_score,
                    team2_score,
                    winner
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)

                ON CONFLICT (faceit_match_id)
                DO UPDATE SET
                    map_name = EXCLUDED.map_name,
                    finished_at = EXCLUDED.finished_at,
                    team1_score = EXCLUDED.team1_score,
                    team2_score = EXCLUDED.team2_score,
                    winner = EXCLUDED.winner

                RETURNING id;
                """,
                (
                    match_id,
                    map_name,
                    finished_at,
                    None,
                    team1_score,
                    team2_score,
                    winner
                )
            )

            match_db_id = result.fetchone()[0]

            # Сохраняем статистику игрока
            connection.execute(
                """
                INSERT INTO player_match_stats (
                    player_id,
                    match_id,
                    kills,
                    deaths,
                    assists,
                    kd,
                    adr,
                    hs_kills,
                    hs_percent,
                    damage,
                    trade_kills,
                    player_team_number
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )

                ON CONFLICT (player_id, match_id)
                DO UPDATE SET
                    kills = EXCLUDED.kills,
                    deaths = EXCLUDED.deaths,
                    assists = EXCLUDED.assists,
                    kd = EXCLUDED.kd,
                    adr = EXCLUDED.adr,
                    hs_kills = EXCLUDED.hs_kills,
                    hs_percent = EXCLUDED.hs_percent,
                    damage = EXCLUDED.damage,
                    trade_kills = EXCLUDED.trade_kills,
                    player_team_number = EXCLUDED.player_team_number;
                """,
                (
                    player_db_id,
                    match_db_id,
                    kills,
                    deaths,
                    assists,
                    kd,
                    adr,
                    hs_kills,
                    hs_percent,
                    damage,
                    trade_kills,
                    player_team_number
                )
            )

            imported += 1

            print("Матч успешно сохранён!")
            print("Карта:", map_name)
            print("Счёт:", team1_score, "-", team2_score)
            print("Победитель:", winner)
            print(
                f"Kills: {kills} | Deaths: {deaths} | "
                f"ADR: {adr} | K/D: {kd}"
            )

    print("\n====================================")
    print("FACEIT IMPORT COMPLETED!")
    print("Импортировано матчей:", imported)
    print("Пропущено матчей:", skipped)
    print("====================================")

    return player_db_id
