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
        try:
            cron_parts = self.config.scheduler.cron.split()
            if len(cron_parts) != 5:
                raise ValueError(
                    f"Cron expression must have exactly 5 parts (minute hour day month day_of_week), "
                    f"got {len(cron_parts)}: '{self.config.scheduler.cron}'"
                )
        except AttributeError:
            raise ValueError(f"Invalid cron expression: '{self.config.scheduler.cron}'")

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
            misfire_grace_time=self.config.scheduler.misfire_grace_time,
            coalesce=True
        )

        logger.info(f"Scheduler started, cron: {self.config.scheduler.cron}")
        job = self.scheduler.get_job("daily_hackernews")
        if job is not None:
            logger.info(f"Next run: {job.next_run_time}")
        else:
            logger.warning("Could not retrieve job to display next run time")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped gracefully")
        except Exception as e:
            logger.error(f"Scheduler encountered an error: {e}")
            raise
