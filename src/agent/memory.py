# src/agent/memory.py
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

import logging

logger = logging.getLogger(__name__)


class Memory:
    """记忆系统 - 存储历史信息，支持检索"""

    def __init__(self, db_path: str = "data/agent_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.short_term: list[dict] = []  # 当前任务记忆
        self._init_db()

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
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
        """初始化数据库"""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    id INTEGER PRIMARY KEY,
                    task TEXT,
                    observation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE,
                    value TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_memory_task
                ON long_term_memory(task);
            """)

    def remember(self, observation: dict):
        """存储观察（短期记忆）"""
        self.short_term.append({
            "timestamp": datetime.now().isoformat(),
            "content": observation
        })

    def save_to_long_term(self, task: str, observation: str):
        """保存到长期记忆"""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "INSERT INTO long_term_memory (task, observation) VALUES (?, ?)",
                    (task, observation)
                )
            logger.info(f"Saved to long-term memory: {task[:50]}...")
        except Exception as e:
            logger.error(f"Failed to save to long-term memory: {e}")

    def recall(self, query: str, limit: int = 5) -> list[dict]:
        """
        检索相关记忆（MVP版本使用关键词匹配）

        Args:
            query: 搜索关键词
            limit: 返回数量限制

        Returns:
            相关记忆列表
        """
        # 从短期记忆中检索
        relevant = [
            m for m in self.short_term
            if query.lower() in str(m["content"]).lower()
        ]

        # 如果短期记忆不够，从长期记忆中检索
        if len(relevant) < limit:
            try:
                with self.get_connection() as conn:
                    rows = conn.execute(
                        "SELECT task, observation, created_at FROM long_term_memory "
                        "WHERE task LIKE ? OR observation LIKE ? "
                        "ORDER BY created_at DESC LIMIT ?",
                        (f"%{query}%", f"%{query}%", limit)
                    ).fetchall()

                    for task, observation, created_at in rows:
                        relevant.append({
                            "timestamp": created_at,
                            "content": {"task": task, "observation": observation}
                        })
            except Exception as e:
                logger.error(f"Failed to recall from long-term memory: {e}")

        return relevant[-limit:]

    def save_user_preference(self, key: str, value: str):
        """保存用户偏好"""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO user_preferences (key, value) VALUES (?, ?)",
                    (key, value)
                )
            logger.info(f"Saved user preference: {key}={value}")
        except Exception as e:
            logger.error(f"Failed to save user preference: {e}")

    def get_user_preference(self, key: str) -> str:
        """获取用户偏好"""
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    "SELECT value FROM user_preferences WHERE key = ?",
                    (key,)
                ).fetchone()
                return row[0] if row else ""
        except Exception as e:
            logger.error(f"Failed to get user preference: {e}")
            return ""

    def clear_short_term(self):
        """清空短期记忆"""
        self.short_term.clear()
