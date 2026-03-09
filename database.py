import sqlite3
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = "bot_database.db"


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self):
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    language TEXT DEFAULT 'en',
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                CREATE INDEX IF NOT EXISTS idx_requests_user_id ON requests(user_id);
                CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at);
            """)
            conn.commit()
        logger.info("Database initialized.")

    def get_user_language(self, user_id: int) -> Optional[str]:
        """Return user's saved language or None if new user."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT language FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            return row["language"] if row else None

    def set_user_language(self, user_id: int, username: Optional[str], language: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO users (user_id, username, language, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    language = excluded.language,
                    last_seen = excluded.last_seen
            """, (user_id, username, language, now, now))
            conn.commit()

    def save_request(self, user_id: int, username: Optional[str], url: str, platform: str) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO users (user_id, username, language, first_seen, last_seen)
                VALUES (?, ?, 'en', ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    last_seen = excluded.last_seen
            """, (user_id, username, now, now))

            cursor = conn.execute("""
                INSERT INTO requests (user_id, url, platform, status, created_at)
                VALUES (?, ?, ?, 'pending', ?)
            """, (user_id, url, platform, now))
            conn.commit()
            return cursor.lastrowid

    def update_request_status(self, request_id: int, status: str, error_message: str = None):
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE requests SET status = ?, error_message = ?
                WHERE id = ?
            """, (status, error_message, request_id))
            conn.commit()

    def get_user_history(self, user_id: int, limit: int = 10) -> list:
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT url, platform, status, created_at
                FROM requests
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit)).fetchall()
            return [dict(row) for row in rows]

    def get_user_stats(self, user_id: int) -> dict:
        with self.get_connection() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM requests
                WHERE user_id = ?
            """, (user_id,)).fetchone()
            return dict(row) if row else {"total": 0, "success": 0, "failed": 0}

    def get_admin_stats(self) -> dict:
        """Full stats for admin."""
        today = datetime.now().strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

            active_today = conn.execute(
                "SELECT COUNT(DISTINCT user_id) FROM requests WHERE created_at LIKE ?",
                (f"{today}%",)
            ).fetchone()[0]

            new_today = conn.execute(
                "SELECT COUNT(*) FROM users WHERE first_seen LIKE ?",
                (f"{today}%",)
            ).fetchone()[0]

            total_downloads = conn.execute(
                "SELECT COUNT(*) FROM requests WHERE status = 'success'"
            ).fetchone()[0]

            total_requests = conn.execute(
                "SELECT COUNT(*) FROM requests"
            ).fetchone()[0]

            tiktok_count = conn.execute(
                "SELECT COUNT(*) FROM requests WHERE platform = 'tiktok' AND status = 'success'"
            ).fetchone()[0]

            instagram_count = conn.execute(
                "SELECT COUNT(*) FROM requests WHERE platform = 'instagram' AND status = 'success'"
            ).fetchone()[0]

            lang_ru = conn.execute(
                "SELECT COUNT(*) FROM users WHERE language = 'ru'"
            ).fetchone()[0]

            lang_en = conn.execute(
                "SELECT COUNT(*) FROM users WHERE language = 'en'"
            ).fetchone()[0]

            downloads_today = conn.execute(
                "SELECT COUNT(*) FROM requests WHERE status = 'success' AND created_at LIKE ?",
                (f"{today}%",)
            ).fetchone()[0]

        return {
            "total_users": total_users,
            "new_today": new_today,
            "active_today": active_today,
            "total_downloads": total_downloads,
            "downloads_today": downloads_today,
            "total_requests": total_requests,
            "tiktok": tiktok_count,
            "instagram": instagram_count,
            "lang_ru": lang_ru,
            "lang_en": lang_en,
        }
