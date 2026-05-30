import logging
from typing import Callable
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from src.config import AppConfig

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self, config: AppConfig, job_func: Callable):
        self.config = config
        self.job_func = job_func
        self.scheduler = BlockingScheduler()

    def start(self) -> None:
        """启动调度器"""
        cron_parts = self.config.scheduler.cron.split()
        trigger = CronTrigger(
            minute=cron_parts[0],
            hour=cron_parts[1],
            day=cron_parts[2],
            month=cron_parts[3],
            day_of_week=cron_parts[4],
            timezone=self.config.scheduler.timezone
        )

        self.scheduler.add_job(
            self.job_func,
            trigger=trigger,
            id="daily_hackernews",
            name="Daily Hacker News Push",
            misfire_grace_time=3600,
            coalesce=True
        )

        logger.info(f"Scheduler started, cron: {self.config.scheduler.cron}")
        job = self.scheduler.get_job("daily_hackernews")
        logger.info(f"Next run: {job.next_run_time}")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped gracefully")
