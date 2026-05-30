import logging
from src.database import Database

logger = logging.getLogger(__name__)

class HealthChecker:
    MAX_RETRIES = 3

    def __init__(self, db: Database):
        self.db = db

    def check_daily_job(self) -> dict:
        """检查每日任务健康状态"""
        try:
            with self.db.get_connection() as conn:
                last_push = conn.execute(
                    "SELECT pushed_at FROM pushed_articles ORDER BY pushed_at DESC LIMIT 1"
                ).fetchone()

                failed_count = conn.execute(
                    "SELECT COUNT(*) FROM failed_pushes WHERE retry_count < ?",
                    (self.MAX_RETRIES,)
                ).fetchone()[0]

                pushed_today = conn.execute(
                    "SELECT COUNT(*) FROM pushed_articles WHERE DATE(pushed_at) = DATE('now')"
                ).fetchone()[0]

            return {
                "last_push": last_push[0] if last_push else None,
                "failed_count": failed_count,
                "pushed_today": pushed_today,
                "healthy": failed_count == 0 and last_push is not None
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "last_push": None,
                "failed_count": 0,
                "pushed_today": 0,
                "healthy": False
            }

    def log_health_status(self):
        """输出健康状态日志"""
        try:
            status = self.check_daily_job()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return
        if status["healthy"]:
            logger.info(f"Health OK | Pushed today: {status['pushed_today']}")
        else:
            logger.warning(
                f"Health Warning | Failed: {status['failed_count']}, "
                f"Last push: {status['last_push']}"
            )
