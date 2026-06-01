import sqlite3
import hashlib
from contextlib import contextmanager
from pathlib import Path
from src.models import Story

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

                CREATE TABLE IF NOT EXISTS cache (
                    id INTEGER PRIMARY KEY,
                    cache_key TEXT UNIQUE,
                    cache_type TEXT,
                    result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_pushed_article_id
                ON pushed_articles(article_id);

                CREATE INDEX IF NOT EXISTS idx_pushed_date
                ON pushed_articles(pushed_at);

                CREATE INDEX IF NOT EXISTS idx_cache_key
                ON cache(cache_key);

                CREATE INDEX IF NOT EXISTS idx_cache_type
                ON cache(cache_type);
            """)

    def get_pushed_ids(self) -> set[int]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT article_id FROM pushed_articles").fetchall()
            return {row[0] for row in rows}

    def record_pushed(self, story: Story):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO pushed_articles (article_id, title) VALUES (?, ?)",
                (story.id, story.title)
            )

    def _make_cache_key(self, cache_type: str, text: str) -> str:
        """生成缓存键"""
        text_hash = hashlib.md5(text.encode()).hexdigest()[:16]
        return f"{cache_type}:{text_hash}"

    def get_cache(self, cache_type: str, text: str) -> str | None:
        """获取缓存"""
        key = self._make_cache_key(cache_type, text)
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT result FROM cache WHERE cache_key = ?",
                (key,)
            ).fetchone()
            return row[0] if row else None

    def set_cache(self, cache_type: str, text: str, result: str):
        """设置缓存"""
        key = self._make_cache_key(cache_type, text)
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (cache_key, cache_type, result) VALUES (?, ?, ?)",
                (key, cache_type, result)
            )

    def clear_old_cache(self, days: int = 7):
        """清理旧缓存"""
        with self.get_connection() as conn:
            conn.execute(
                "DELETE FROM cache WHERE created_at < datetime('now', ?)",
                (f"-{days} days",)
            )
