import sqlite3
import logging
from typing import Optional, List, Dict
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_message_sent TIMESTAMP
                )
            """)
            
            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Initialize default settings
            default_settings = {
                "channel_link": "https://t.me/bigmumbaiofficial",
                "button_text": "Join Big Mumbai Channel",
                "file_button_text": "📥 Download Files",
                "caption_text": "Welcome to Big Mumbai Official! Join our channel to stay updated.",
                "image_file_id": None,
                "file_id": None,
                "file_type": None,
                "file_name": None,
                "file_caption": None,
                "auto_message_text": "Don't forget to join our channel for latest updates!",
                "interval_hours": "8",
                "auto_messages_enabled": "1"
            }
            
            for key, value in default_settings.items():
                cursor.execute(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                    (key, str(value))
                )
            
            conn.commit()
            logger.info("Database initialized successfully")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def add_user(self, user_id: int, username: Optional[str] = None, first_name: Optional[str] = None):
        """Add or update user in database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO users (user_id, username, first_name, is_active)
                VALUES (?, ?, ?, 1)
            """, (user_id, username, first_name))
            logger.info(f"User {user_id} added/updated in database")

    def get_active_users(self) -> List[Dict]:
        """Get all active users"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, first_name FROM users WHERE is_active = 1")
            return [dict(row) for row in cursor.fetchall()]

    def mark_user_inactive(self, user_id: int):
        """Mark user as inactive"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,))
            logger.info(f"User {user_id} marked as inactive")

    def update_last_message_sent(self, user_id: int):
        """Update last message sent timestamp"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET last_message_sent = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )

    def get_setting(self, key: str) -> Optional[str]:
        """Get setting value by key"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else None

    def set_setting(self, key: str, value: str):
        """Set setting value"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            logger.info(f"Setting {key} updated to {value}")

    def get_stats(self) -> Dict:
        """Get bot statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM users")
            total_users = cursor.fetchone()["total"]
            
            cursor.execute("SELECT COUNT(*) as active FROM users WHERE is_active = 1")
            active_users = cursor.fetchone()["active"]
            
            return {
                "total_users": total_users,
                "active_users": active_users
            }

