
from services.database import get_connection


# Общая статистика
def get_overall_stats(player_db_id):

    with get_connection() as connection:

        result = connection.execute(
            """
            SELECT
                COUNT(*) AS matches_played,
                COALESCE(SUM(s.kills), 0) AS total_kills,
                COALESCE(SUM(s.deaths), 0) AS total_deaths,
                COALESCE(SUM(s.assists), 0) AS total_assists,

                ROUND(
                    SUM(s.kills)::numeric /
                    NULLIF(SUM(s.deaths), 0), 2
                ) AS overall_kd,

                ROUND(AVG(s.adr), 2) AS average_adr,

                ROUND(
                    SUM(s.hs_kills)::numeric * 100 /
                    NULLIF(SUM(s.kills), 0), 2
                ) AS hs_percent,

                COALESCE(SUM(s.damage), 0) AS total_damage,

                ROUND(AVG(s.kills), 2) AS average_kills,
                ROUND(AVG(s.deaths), 2) AS average_deaths,
                ROUND(AVG(s.assists), 2) AS average_assists

            FROM player_match_stats s
            WHERE s.player_id = %s;
            """,
            (player_db_id,)
        )

        row = result.fetchone()

        columns = [
            "matches_played",
            "total_kills",
            "total_deaths",
            "total_assists",
            "overall_kd",
            "average_adr",
            "hs_percent",
            "total_damage",
            "average_kills",
            "average_deaths",
            "average_assists"
        ]

        return dict(zip(columns, row))


# Статистика по картам
def get_map_stats(player_db_id):

    with get_connection() as connection:

        result = connection.execute(
            """
            SELECT
                m.map_name,
                COUNT(*) AS matches_played,
                ROUND(AVG(s.kills), 2) AS avg_kills,
                ROUND(AVG(s.deaths), 2) AS avg_deaths,
                ROUND(AVG(s.kd), 2) AS avg_kd,
                ROUND(AVG(s.adr), 2) AS avg_adr,
                ROUND(AVG(s.hs_percent), 2) AS avg_hs_percent

            FROM player_match_stats s
            JOIN matches m ON m.id = s.match_id

            WHERE s.player_id = %s

            GROUP BY m.map_name
            ORDER BY matches_played DESC;
            """,
            (player_db_id,)
        )

        return result.fetchall()


# Победы, поражения и Win Rate
def get_win_stats(player_db_id):

    with get_connection() as connection:

        result = connection.execute(
            """
            SELECT
                COUNT(*) FILTER (
                    WHERE m.winner IN ('1', '2')
                ) AS completed_matches,

                COUNT(*) FILTER (
                    WHERE m.winner = s.player_team_number::text
                ) AS wins,

                COUNT(*) FILTER (
                    WHERE m.winner IN ('1', '2')
                    AND m.winner != s.player_team_number::text
                ) AS losses,

                ROUND(
                    COUNT(*) FILTER (
                        WHERE m.winner = s.player_team_number::text
                    )::numeric * 100 /
                    NULLIF(
                        COUNT(*) FILTER (
                            WHERE m.winner IN ('1', '2')
                        ), 0
                    ),
                    2
                ) AS win_rate

            FROM player_match_stats s
            JOIN matches m ON m.id = s.match_id

            WHERE s.player_id = %s;
            """,
            (player_db_id,)
        )

        row = result.fetchone()

        columns = [
            "completed_matches",
            "wins",
            "losses",
            "win_rate"
        ]

        return dict(zip(columns, row))


# Последние матчи
def get_recent_matches(player_db_id, limit=10):

    with get_connection() as connection:

        result = connection.execute(
            """
            SELECT
                m.map_name,
                m.finished_at,

                CASE
                    WHEN s.player_team_number = 1
                    THEN m.team1_score
                    WHEN s.player_team_number = 2
                    THEN m.team2_score
                END AS player_score,

                CASE
                    WHEN s.player_team_number = 1
                    THEN m.team2_score
                    WHEN s.player_team_number = 2
                    THEN m.team1_score
                END AS opponent_score,

                CASE
                    WHEN m.winner IS NULL THEN 'UNKNOWN'
                    WHEN m.winner = s.player_team_number::text
                    THEN 'WIN'
                    ELSE 'LOSS'
                END AS match_result,

                s.kills,
                s.deaths,
                s.assists,
                s.kd,
                s.adr,
                s.hs_percent

            FROM player_match_stats s
            JOIN matches m ON m.id = s.match_id

            WHERE s.player_id = %s

            ORDER BY m.finished_at DESC
            LIMIT %s;
            """,
            (player_db_id, limit)
        )

        return result.fetchall()
