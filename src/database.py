import sqlite3
from contextlib import contextmanager
from pathlib import Path

class Database:
    def __init__(self, db_path: str = "data/hackernews.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS pushed_articles (
                    id INTEGER PRIMARY KEY,
                    article_id INTEGER UNIQUE,
                    title TEXT,
                    pushed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS failed_pushes (
                    id INTEGER PRIMARY KEY,
                    message TEXT,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    retry_count INTEGER DEFAULT 0
                );
            """)

    def get_pushed_ids(self) -> set[int]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT article_id FROM pushed_articles").fetchall()
            return {row[0] for row in rows}

    def record_pushed(self, article_id: int, title: str):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO pushed_articles (article_id, title) VALUES (?, ?)",
                (article_id, title)
            )
