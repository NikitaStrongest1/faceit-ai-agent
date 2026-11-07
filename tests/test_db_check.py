
from services.database import get_connection

with get_connection() as connection:

    rows = connection.execute(
        """
        SELECT
            p.nickname,
            m.faceit_match_id,
            m.map_name,
            m.team1_score,
            m.team2_score,
            m.winner,
            pms.player_team_number,
            pms.kills,
            pms.deaths,
            pms.adr
        FROM player_match_stats pms
        JOIN players p ON p.id = pms.player_id
        JOIN matches m ON m.id = pms.match_id
        WHERE p.nickname = %s
        ORDER BY m.finished_at DESC
        LIMIT 20;
        """,
        ("yan_toplec",)
    ).fetchall()

    print("\n========== FACEIT MATCHES ==========\n")

    for row in rows:
        print(row)

    print("\nВсего матчей:", len(rows))
