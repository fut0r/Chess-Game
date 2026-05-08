"""
backend/database.py - PostgreSQL database layer
Connection pool, schema creation, and data access methods.
Uses psycopg v3 (async-capable).
"""

import psycopg
from psycopg.rows import dict_row
import os
import json

# Database config — override with environment variables
DB_HOST = os.getenv("CHESS_DB_HOST", "localhost")
DB_PORT = os.getenv("CHESS_DB_PORT", "3000")
DB_NAME = os.getenv("CHESS_DB_NAME", "chess_game")
DB_USER = os.getenv("CHESS_DB_USER", "postgres")
DB_PASS = os.getenv("CHESS_DB_PASS", "1234")

CONNINFO = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASS} connect_timeout=3"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(32) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    display_name VARCHAR(64),
    elo_rating INT DEFAULT 1200,
    games_played INT DEFAULT 0,
    games_won INT DEFAULT 0,
    games_drawn INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS achievements (
    id VARCHAR(48) PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    description TEXT NOT NULL,
    icon VARCHAR(16) NOT NULL,
    category VARCHAR(24) NOT NULL,
    rarity VARCHAR(16) DEFAULT 'common'
);

CREATE TABLE IF NOT EXISTS user_achievements (
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    achievement_id VARCHAR(48) REFERENCES achievements(id) ON DELETE CASCADE,
    unlocked_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, achievement_id)
);

CREATE TABLE IF NOT EXISTS game_history (
    id SERIAL PRIMARY KEY,
    white_user_id INT REFERENCES users(id),
    black_user_id INT,
    result VARCHAR(16),
    result_reason VARCHAR(32),
    moves_count INT,
    time_control VARCHAR(32),
    played_at TIMESTAMP DEFAULT NOW()
);
"""


class Database:
    """PostgreSQL database manager."""

    def __init__(self):
        self.conn = None

    def connect(self):
        """Connect to the database."""
        try:
            self.conn = psycopg.connect(CONNINFO, row_factory=dict_row)
            self.conn.autocommit = True
            return True
        except Exception as e:
            print(f"[DB] Connection failed: {e}")
            return False

    def close(self):
        if self.conn:
            self.conn.close()

    def init_schema(self):
        """Create tables if they don't exist."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
            return True
        except Exception as e:
            print(f"[DB] Schema init failed: {e}")
            return False

    def seed_achievements(self, achievements_list):
        """Insert achievement definitions (upsert)."""
        try:
            with self.conn.cursor() as cur:
                for ach in achievements_list:
                    cur.execute("""
                        INSERT INTO achievements (id, name, description, icon, category, rarity)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            icon = EXCLUDED.icon,
                            category = EXCLUDED.category,
                            rarity = EXCLUDED.rarity
                    """, (ach['id'], ach['name'], ach['description'],
                          ach['icon'], ach['category'], ach['rarity']))
            return True
        except Exception as e:
            print(f"[DB] Seed achievements failed: {e}")
            return False

    # -----------------------------------------------------------------------
    # Users
    # -----------------------------------------------------------------------
    def create_user(self, username, password_hash, display_name=None):
        """Create a new user. Returns user dict or None."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (username, password_hash, display_name)
                    VALUES (%s, %s, %s)
                    RETURNING id, username, display_name, elo_rating,
                              games_played, games_won, games_drawn, created_at
                """, (username, password_hash, display_name or username))
                return cur.fetchone()
        except psycopg.errors.UniqueViolation:
            return None
        except Exception as e:
            print(f"[DB] Create user failed: {e}")
            return None

    def get_user_by_username(self, username):
        """Get user by username."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cur.fetchone()

    def get_user_by_id(self, user_id):
        """Get user by ID."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cur.fetchone()

    def update_user_stats(self, user_id, games_played=0, games_won=0, games_drawn=0, new_elo=None):
        """Increment user stats and optionally update ELO."""
        with self.conn.cursor() as cur:
            if new_elo is not None:
                cur.execute("""
                    UPDATE users SET
                        games_played = games_played + %s,
                        games_won = games_won + %s,
                        games_drawn = games_drawn + %s,
                        elo_rating = %s
                    WHERE id = %s
                """, (games_played, games_won, games_drawn, new_elo, user_id))
            else:
                cur.execute("""
                    UPDATE users SET
                        games_played = games_played + %s,
                        games_won = games_won + %s,
                        games_drawn = games_drawn + %s
                    WHERE id = %s
                """, (games_played, games_won, games_drawn, user_id))

    def update_elo(self, user_id, new_elo):
        """Update ELO rating."""
        with self.conn.cursor() as cur:
            cur.execute("UPDATE users SET elo_rating = %s WHERE id = %s",
                        (new_elo, user_id))

    # -----------------------------------------------------------------------
    # Achievements
    # -----------------------------------------------------------------------
    def get_all_achievements(self):
        """Get all achievement definitions."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM achievements ORDER BY category, id")
            return cur.fetchall()

    def get_user_achievements(self, user_id):
        """Get achievements unlocked by a user."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT a.*, ua.unlocked_at
                FROM user_achievements ua
                JOIN achievements a ON a.id = ua.achievement_id
                WHERE ua.user_id = %s
                ORDER BY ua.unlocked_at DESC
            """, (user_id,))
            return cur.fetchall()

    def unlock_achievement(self, user_id, achievement_id):
        """Unlock an achievement for a user. Returns True if newly unlocked."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_achievements (user_id, achievement_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (user_id, achievement_id))
                return cur.rowcount > 0
        except Exception:
            return False

    def is_achievement_unlocked(self, user_id, achievement_id):
        """Check if user has an achievement."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT 1 FROM user_achievements
                WHERE user_id = %s AND achievement_id = %s
            """, (user_id, achievement_id))
            return cur.fetchone() is not None

    # -----------------------------------------------------------------------
    # Game History
    # -----------------------------------------------------------------------
    def record_game(self, white_user_id, black_user_id, result,
                    result_reason, moves_count, time_control):
        """Record a completed game."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO game_history
                    (white_user_id, black_user_id, result, result_reason,
                     moves_count, time_control)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (white_user_id, black_user_id, result,
                  result_reason, moves_count, time_control))
            return cur.fetchone()

    def get_user_games(self, user_id, limit=50):
        """Get recent games for a user."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM game_history
                WHERE white_user_id = %s OR black_user_id = %s
                ORDER BY played_at DESC LIMIT %s
            """, (user_id, user_id, limit))
            return cur.fetchall()

    def get_leaderboard(self, limit=20):
        """Get top players by ELO."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, display_name, elo_rating,
                       games_played, games_won
                FROM users
                WHERE games_played > 0
                ORDER BY elo_rating DESC LIMIT %s
            """, (limit,))
            return cur.fetchall()
