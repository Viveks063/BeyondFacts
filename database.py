"""
Database Manager for Beyond Facts AI Agent.
Manages the `posts` table in `history.db` to prevent duplicate posts,
track publication status, and store engagement analytics.
"""

import sqlite3
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger("DatabaseManager")


class DatabaseManager:
    """Manages SQLite operations for scheduled posts and analytics tracking."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes the database table with exact requested schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Main posts table as requested in user architecture
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    category TEXT NOT NULL,
                    caption TEXT,
                    image TEXT,
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'PENDING',
                    instagram_post_id TEXT,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    saves INTEGER DEFAULT 0,
                    time_slot TEXT
                )
            """)
            
            # Legacy table compatibility (post_history) if present
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS post_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    category TEXT,
                    caption TEXT,
                    image_url TEXT,
                    platform TEXT,
                    platform_post_id TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def is_slot_posted_today(self, slot_time: str, date_str: Optional[str] = None) -> bool:
        """
        Checks if a post has already been generated or published for the given time slot today.
        Prevents duplicate posts.
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM posts 
                WHERE time_slot = ? 
                  AND DATE(posted_at) = DATE(?) 
                  AND status IN ('PUBLISHED', 'PENDING', 'PROCESSING')
            """, (slot_time, date_str))
            row = cursor.fetchone()
            return row is not None

    def create_post_record(
        self,
        topic: str,
        category: str,
        caption: str,
        image: str,
        time_slot: str,
        status: str = "PENDING"
    ) -> int:
        """Inserts a new post record into the database."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO posts (topic, category, caption, image, posted_at, status, time_slot)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (topic, category, caption, image, now_str, status, time_slot))
            post_id = cursor.lastrowid

            # Also mirror to post_history for legacy query safety
            cursor.execute("""
                INSERT INTO post_history (topic, category, caption, image_url, platform, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (topic, category, caption, image, "Instagram", status))

            conn.commit()
            logger.info(f"Created post record #{post_id} for slot '{time_slot}' [{category}: {topic}]")
            return post_id

    def update_post_status(
        self,
        post_id: int,
        status: str,
        instagram_post_id: Optional[str] = None,
        image_url: Optional[str] = None
    ):
        """Updates the publication status and Instagram post ID of a record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if image_url and instagram_post_id:
                cursor.execute("""
                    UPDATE posts 
                    SET status = ?, instagram_post_id = ?, image = ?
                    WHERE id = ?
                """, (status, instagram_post_id, image_url, post_id))
            elif instagram_post_id:
                cursor.execute("""
                    UPDATE posts 
                    SET status = ?, instagram_post_id = ?
                    WHERE id = ?
                """, (status, instagram_post_id, post_id))
            else:
                cursor.execute("""
                    UPDATE posts 
                    SET status = ?
                    WHERE id = ?
                """, (status, post_id))
            conn.commit()
            logger.info(f"Updated post #{post_id} status to '{status}' (IG ID: {instagram_post_id})")

    def update_post_metrics(
        self,
        post_id: int,
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
        saves: int = 0
    ):
        """Updates performance metrics for a specific post."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE posts 
                SET likes = ?, comments = ?, shares = ?, saves = ?
                WHERE id = ?
            """, (likes, comments, shares, saves, post_id))
            conn.commit()

    def get_all_posts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent post records from the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, topic, category, caption, image, posted_at, status, instagram_post_id, likes, comments, shares, saves, time_slot
                FROM posts
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_category_performance_summary(self) -> List[Dict[str, Any]]:
        """Calculates total engagement metrics grouped by category for AI agent feedback loop."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    category,
                    COUNT(*) as total_posts,
                    SUM(likes) as total_likes,
                    SUM(comments) as total_comments,
                    SUM(shares) as total_shares,
                    SUM(saves) as total_saves,
                    (SUM(saves) * 5 + SUM(comments) * 3 + SUM(shares) * 4 + SUM(likes) * 1) as performance_score
                FROM posts
                WHERE status = 'PUBLISHED'
                GROUP BY category
                ORDER BY performance_score DESC
            """)
            return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    db = DatabaseManager()
    posts = db.get_all_posts()
    print(f"Total posts in database: {len(posts)}")
