import os
from pathlib import Path
import psycopg
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


if __name__ == "__main__":
    with get_connection() as connection:
        result = connection.execute(
            "SELECT current_database();"
        ).fetchone()

        print("Подключение успешно!")
        print("Database:", result[0])


def save_player(player):
    cs2 = player.get("games", {}).get("cs2", {})

    with get_connection() as connection:
        result = connection.execute(
            """
            INSERT INTO players (
                faceit_player_id,
                nickname,
                steam_id,
                country,
                current_elo
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (faceit_player_id)
            DO UPDATE SET
                nickname = EXCLUDED.nickname,
                steam_id = EXCLUDED.steam_id,
                country = EXCLUDED.country,
                current_elo = EXCLUDED.current_elo,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id;
            """,
            (
                player["player_id"],
                player["nickname"],
                cs2.get("game_player_id"),
                player.get("country"),
                cs2.get("faceit_elo")
            )
        )

        player_db_id = result.fetchone()[0]

    print("Игрок сохранён в PostgreSQL!")

    return player_db_id
