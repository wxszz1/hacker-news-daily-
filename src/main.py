import time
import logging
import threading
from contextlib import contextmanager
from typing import Optional
from dotenv import load_dotenv

from src.config import load_config, AppConfig
from src.logging_config import setup_logging
from src.scraper import HackerNewsScraper
from src.filter import NewsFilter
from src.formatter import MessageFormatter
from src.notifier import ServerChanNotifier
from src.database import Database
from src.health import HealthChecker
from src.scheduler import Scheduler
from src.llm_client import LLMClient
from src.scorer import Scorer
from src.summarizer import Summarizer
from src.researcher import Researcher
from src.models import Story

logger = logging.getLogger(__name__)

@contextmanager
def timer(operation: str):
    """执行时间统计上下文管理器"""
    start = time.time()
    yield
    duration = time.time() - start
    logger.info(f"{operation} completed in {duration:.2f}s")

def run_job() -> None:
    """单次执行任务（带异常处理）"""
    try:
        with timer("Total job"):
            _execute_job()
    except Exception as e:
        logger.exception(f"Job failed: {e}")
        _notify_failure(e)

def _execute_job() -> None:
    """执行任务核心逻辑"""
    load_dotenv()
    config = load_config()
    db = Database(config.database.path)

    # 清理旧缓存
    db.clear_old_cache(days=7)

    stories = _fetch_stories(config)
    filtered = _filter_stories(config, stories, db)

    if not filtered:
        logger.info("No new stories to push")
        return

    # Agent 处理：评分、摘要、研究
    enriched = _agent_process(config, filtered, db)

    _push_stories(config, enriched, db)

def _fetch_stories(config: AppConfig) -> list[Story]:
    """爬取阶段"""
    with timer("Fetch stories"):
        scraper = HackerNewsScraper()
        stories = scraper.fetch_top_stories_sync(config.hackernews.top_stories_limit)
        logger.info(f"Fetched {len(stories)} stories")
        return stories

def _filter_stories(
    config: AppConfig,
    stories: list[Story],
    db: Database
) -> list[Story]:
    """过滤阶段"""
    with timer("Filter stories"):
        news_filter = NewsFilter(config.filter)
        pushed_ids = db.get_pushed_ids()
        filtered = news_filter.filter(stories, pushed_ids)
        logger.info(f"After filter: {len(filtered)} stories")
        return filtered

def _agent_process(config: AppConfig, stories: list[Story], db: Database) -> list[Story]:
    """Agent 处理：评分、摘要、研究（带错误隔离）"""
    if not config.agent.enabled:
        return stories

    with timer("Agent processing"):
        llm_client = LLMClient(config.agent.llm)

        if not llm_client.enabled:
            logger.warning("LLM API key not set, skipping agent processing")
            return stories

        scorer = Scorer(llm_client, config.agent.scorer)
        summarizer = Summarizer(llm_client, config.agent.summarizer, db)
        researcher = Researcher(llm_client, config.agent.researcher)

        # 1. 重要性评分（带错误隔离）
        logger.info("Scoring stories...")
        try:
            scores = scorer.score_batch(stories)
            for story, score_info in zip(stories, scores):
                story.agent_score = score_info["importance"]
                story.agent_score_reason = score_info["reason"]
        except Exception as e:
            logger.error(f"Scoring failed, skipping: {e}")

        # 2. 智能摘要（带错误隔离）
        logger.info("Generating summaries...")
        try:
            summaries = summarizer.summarize_batch(stories)
            for story, summary_info in zip(stories, summaries):
                story.summary = summary_info.get("summary", "")
                story.key_points = summary_info.get("key_points", [])
        except Exception as e:
            logger.error(f"Summarization failed, skipping: {e}")

        # 3. 深度研究（仅高分文章，带错误隔离）
        logger.info("Researching high-score articles...")
        try:
            research_results = researcher.research_batch(stories)
            for story, research_info in zip(stories, research_results):
                story.research_report = research_info.get("report", "")
                story.research_highlights = research_info.get("highlights", [])
        except Exception as e:
            logger.error(f"Research failed, skipping: {e}")

        logger.info("Agent processing completed")
        return stories

def _push_stories(
    config: AppConfig,
    stories: list[Story],
    db: Database
) -> None:
    """推送阶段"""
    with timer("Push stories"):
        # 创建 LLM 客户端用于分类
        llm_client = LLMClient(config.agent.llm) if config.agent.enabled else None
        formatter = MessageFormatter(llm_client=llm_client, db=db)
        message = formatter.format(stories)

        if not message:
            logger.warning("Formatter returned empty message, skipping push")
            return

        notifier = ServerChanNotifier(config.serverchan.send_key, db)
        title = f"Hacker News 早报 ({len(stories)} 条)"

        if notifier.send(title, message):
            for story in stories:
                db.record_pushed(story)
            logger.info(f"Pushed {len(stories)} stories successfully")
        else:
            logger.error("Push failed, will retry next time")

def _notify_failure(error: Exception) -> None:
    """失败通知"""
    logger.error(f"Job failed: {error}")

def retry_failed_async(config: AppConfig, db: Database) -> None:
    """异步重试失败记录（不阻塞启动）"""
    def _retry():
        try:
            notifier = ServerChanNotifier(config.serverchan.send_key, db)
            notifier.retry_failed()
            logger.info("Retry failed pushes completed")
        except Exception as e:
            logger.exception(f"Retry thread failed: {e}")

    thread = threading.Thread(target=_retry, daemon=True)
    thread.start()

def main() -> None:
    """主函数"""
    load_dotenv()
    config = load_config()
    setup_logging(config.logging.model_dump())

    logger.info("Hacker News Agent starting...")

    db = Database(config.database.path)

    # 健康检查
    health = HealthChecker(db)
    health.log_health_status()

    # 异步重试失败记录
    retry_failed_async(config, db)

    # 启动调度器
    scheduler = Scheduler(config, run_job)
    scheduler.start()

if __name__ == "__main__":
    main()
