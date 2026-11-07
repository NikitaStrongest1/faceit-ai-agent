
import os
from pathlib import Path

import psycopg
from psycopg import sql
from dotenv import load_dotenv


# Загружаем настройки
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "faceit_analytics")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def create_database():

    if not DB_PASSWORD:
        raise ValueError("Не указан DB_PASSWORD в файле .env")

    # Подключаемся к служебной базе PostgreSQL
    print("Подключаемся к PostgreSQL...")

    with psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        autocommit=True
    ) as connection:

        # Проверяем существование базы
        result = connection.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_NAME,)
        ).fetchone()

        if result:
            print(f"База {DB_NAME} уже существует.")
        else:
            connection.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(DB_NAME)
                )
            )
            print(f"База {DB_NAME} успешно создана.")

    # Подключаемся к нашей базе
    print("\nСоздаём таблицы...")

    with psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    ) as connection:

        # 1. Игроки
        connection.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id BIGSERIAL PRIMARY KEY,
                faceit_player_id VARCHAR(100) UNIQUE NOT NULL,
                nickname VARCHAR(100) NOT NULL,
                steam_id VARCHAR(32),
                country VARCHAR(10),
                current_elo INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Матчи
        connection.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id BIGSERIAL PRIMARY KEY,
                faceit_match_id VARCHAR(150) UNIQUE NOT NULL,
                map_name VARCHAR(100),
                started_at TIMESTAMPTZ,
                finished_at TIMESTAMPTZ,
                rounds_played INTEGER,
                team1_score INTEGER,
                team2_score INTEGER,
                winner VARCHAR(100),
                demo_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 3. Статистика игрока в матче
        connection.execute("""
            CREATE TABLE IF NOT EXISTS player_match_stats (
                id BIGSERIAL PRIMARY KEY,

                player_id BIGINT NOT NULL
                    REFERENCES players(id) ON DELETE CASCADE,

                match_id BIGINT NOT NULL
                    REFERENCES matches(id) ON DELETE CASCADE,

                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,

                kd NUMERIC(6, 2),
                adr NUMERIC(6, 2),
                hs_kills INTEGER DEFAULT 0,
                hs_percent NUMERIC(6, 2),
                kast NUMERIC(6, 2),
                damage INTEGER DEFAULT 0,

                opening_kills INTEGER DEFAULT 0,
                opening_deaths INTEGER DEFAULT 0,
                trade_kills INTEGER DEFAULT 0,

                clutches_played INTEGER DEFAULT 0,
                clutches_won INTEGER DEFAULT 0,

                ct_kills INTEGER DEFAULT 0,
                ct_deaths INTEGER DEFAULT 0,
                t_kills INTEGER DEFAULT 0,
                t_deaths INTEGER DEFAULT 0,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (player_id, match_id)
            );
        """)

        # 4. Статистика по позициям
        connection.execute("""
            CREATE TABLE IF NOT EXISTS position_stats (
                id BIGSERIAL PRIMARY KEY,

                player_id BIGINT NOT NULL
                    REFERENCES players(id) ON DELETE CASCADE,

                match_id BIGINT NOT NULL
                    REFERENCES matches(id) ON DELETE CASCADE,

                position_name VARCHAR(100) NOT NULL,

                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,

                kd NUMERIC(6, 2),

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (player_id, match_id, position_name)
            );
        """)

        # Индексы для ускорения запросов
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_matches_map
            ON matches(map_name);
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_player_stats_player
            ON player_match_stats(player_id);
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_player_stats_match
            ON player_match_stats(match_id);
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_positions_player
            ON position_stats(player_id);
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_positions_match
            ON position_stats(match_id);
        """)

    print("\n" + "=" * 45)
    print("DATABASE CREATED SUCCESSFULLY!")
    print("=" * 45)
    print("Database:", DB_NAME)
    print("Tables:")
    print("1. players")
    print("2. matches")
    print("3. player_match_stats")
    print("4. position_stats")
    print("\nAll tables and indexes are ready!")


if __name__ == "__main__":
    create_database()
