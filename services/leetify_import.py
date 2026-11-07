
from services.faceit_api import get_player
from services.leetify_api import get_player_matches
from services.database import get_connection, save_player


def import_matches(nickname):
    print("\nПолучаем профиль FACEIT...")

    player = get_player(nickname)

    if not player:
        print("Игрок не найден!")
        return None

    # Получаем Steam ID из профиля FACEIT
    cs2_data = player.get("games", {}).get("cs2", {})
    steam_id = cs2_data.get("game_player_id")

    if not steam_id:
        print("У игрока не найден Steam ID.")
        return None

    # Сохраняем или обновляем игрока
    save_player(player)

    print("Игрок:", player.get("nickname"))
    print("Steam ID:", steam_id)

    print("\nПолучаем матчи из Leetify...")

    matches = get_player_matches(steam_id)

    if not matches:
        print("Матчи не найдены.")
        return steam_id

    print("Получено матчей:", len(matches))

    with get_connection() as connection:

        # Находим ID игрока в нашей базе
        player_db = connection.execute(
            """
            SELECT id
            FROM players
            WHERE steam_id = %s;
            """,
            (steam_id,)
        ).fetchone()

        if not player_db:
            print("Игрок не найден в PostgreSQL!")
            return None

        player_db_id = player_db[0]
        imported = 0

        for match in matches:

            match_id = match.get("data_source_match_id")

            if not match_id:
                continue

            # Находим статистику выбранного игрока
            player_stats = None

            for stats in match.get("stats", []):
                if str(stats.get("steam64_id")) == str(steam_id):
                    player_stats = stats
                    break

            if not player_stats:
                continue

            # Получаем счёт команд
            team_scores = {
                int(team["team_number"]): team["score"]
                for team in match.get("team_scores", [])
            }

            team1_score = team_scores.get(2)
            team2_score = team_scores.get(3)

            winner = None

            if team1_score is not None and team2_score is not None:
                if team1_score > team2_score:
                    winner = "2"
                elif team2_score > team1_score:
                    winner = "3"
                else:
                    winner = "draw"

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
                    rounds_played = EXCLUDED.rounds_played,
                    team1_score = EXCLUDED.team1_score,
                    team2_score = EXCLUDED.team2_score,
                    winner = EXCLUDED.winner

                RETURNING id;
                """,
                (
                    match_id,
                    match.get("map_name"),
                    match.get("finished_at"),
                    player_stats.get("rounds_count"),
                    team1_score,
                    team2_score,
                    winner
                )
            )

            match_db_id = result.fetchone()[0]

            # Рассчитываем HS%
            kills = player_stats.get("total_kills", 0) or 0
            hs_kills = player_stats.get("total_hs_kills", 0) or 0

            hs_percent = (
                hs_kills / kills * 100
                if kills > 0 else 0
            )

            player_team_number = player_stats.get("initial_team_number")

            if player_team_number is not None:
                player_team_number = int(player_team_number)

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
                    player_stats.get("total_deaths"),
                    player_stats.get("total_assists"),
                    player_stats.get("kd_ratio"),
                    player_stats.get("dpr"),
                    hs_kills,
                    hs_percent,
                    player_stats.get("total_damage"),
                    player_stats.get("trade_kills_succeed"),
                    player_team_number
                )
            )

            imported += 1

        print("--------------------------------")
        print("IMPORT COMPLETED!")
        print("Processed matches:", imported)
        print("--------------------------------")

    return steam_id
