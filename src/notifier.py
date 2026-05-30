import httpx
import time
import logging

logger = logging.getLogger(__name__)

class ServerChanNotifier:
    API_URL = "https://sctapi.ftqq.com/{key}.send"
    MAX_RETRIES = 3

    def __init__(self, send_key: str, db):
        self.send_key = send_key
        self.db = db

    def send(self, title: str, content: str) -> bool:
        """推送消息，失败时记录到 SQLite"""
        for attempt in range(self.MAX_RETRIES):
            try:
                resp = httpx.post(
                    self.API_URL.format(key=self.send_key),
                    data={"title": title, "desp": content}
                )
                if resp.status_code == 200:
                    return True
            except Exception as e:
                logger.warning(f"Push attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)

        self._record_failure(title, content)
        return False

    def _record_failure(self, title: str, content: str):
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO failed_pushes (message, error) VALUES (?, ?)",
                (f"{title}\n{content}", "max retries exceeded")
            )

    def retry_failed(self):
        """重试失败的推送"""
        with self.db.get_connection() as conn:
            failures = conn.execute(
                "SELECT id, message FROM failed_pushes WHERE retry_count < ?",
                (self.MAX_RETRIES,)
            ).fetchall()

        for failure_id, message in failures:
            parts = message.split("\n", 1)
            if len(parts) < 2:
                title = parts[0]
                content = ""
            else:
                title, content = parts

            success = self.send(title, content)

            with self.db.get_connection() as conn:
                if success:
                    conn.execute(
                        "DELETE FROM failed_pushes WHERE id = ?",
                        (failure_id,)
                    )
                else:
                    conn.execute(
                        "UPDATE failed_pushes SET retry_count = retry_count + 1 WHERE id = ?",
                        (failure_id,)
                    )
