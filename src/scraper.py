import httpx
import time
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class HackerNewsScraper:
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    REQUEST_DELAY = 0.1
    TIMEOUT = 10.0

    def __init__(self) -> None:
        pass

    def fetch_top_stories_sync(self, limit: int = 30) -> list[dict]:
        """同步获取 top stories"""
        try:
            with httpx.Client(timeout=self.TIMEOUT) as client:
                story_ids = self._fetch_ids_sync(client, "topstories")
                if not story_ids:
                    logger.warning("No story IDs fetched")
                    return []

                results = []
                for sid in story_ids[:limit]:
                    story = self._get_story_detail_sync(client, sid)
                    if story:
                        results.append(story)
                return results
        except httpx.TimeoutException:
            logger.error("Timeout fetching stories from HN API")
            return []
        except httpx.RequestError as e:
            logger.error(f"Network error fetching stories: {e}")
            return []

    async def fetch_top_stories(self, limit: int = 30) -> list[dict]:
        """异步获取 top stories"""
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                story_ids = await self._fetch_ids_async(client, "topstories")
                if not story_ids:
                    logger.warning("No story IDs fetched")
                    return []

                tasks = [self._get_story_detail_async(client, sid) for sid in story_ids[:limit]]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return [r for r in results if isinstance(r, dict)]
        except httpx.TimeoutException:
            logger.error("Timeout fetching stories from HN API")
            return []
        except httpx.RequestError as e:
            logger.error(f"Network error fetching stories: {e}")
            return []

    def _fetch_ids_sync(self, client: httpx.Client, endpoint: str) -> list[int]:
        """同步获取故事 ID 列表"""
        try:
            resp = client.get(f"{self.BASE_URL}/{endpoint}.json")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch IDs: {e}")
            return []

    async def _fetch_ids_async(self, client: httpx.AsyncClient, endpoint: str) -> list[int]:
        """异步获取故事 ID 列表"""
        try:
            resp = await client.get(f"{self.BASE_URL}/{endpoint}.json")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch IDs: {e}")
            return []

    def _get_story_detail_sync(self, client: httpx.Client, story_id: int) -> Optional[dict]:
        """同步获取单条故事详情"""
        time.sleep(self.REQUEST_DELAY)
        try:
            resp = client.get(f"{self.BASE_URL}/item/{story_id}.json")
            resp.raise_for_status()
            data = resp.json()
            if data is None:
                logger.warning(f"Story {story_id} not found")
                return None
            return data
        except Exception as e:
            logger.error(f"Failed to fetch story {story_id}: {e}")
            return None

    async def _get_story_detail_async(self, client: httpx.AsyncClient, story_id: int) -> Optional[dict]:
        """异步获取单条故事详情"""
        await asyncio.sleep(self.REQUEST_DELAY)
        try:
            resp = await client.get(f"{self.BASE_URL}/item/{story_id}.json")
            resp.raise_for_status()
            data = resp.json()
            if data is None:
                logger.warning(f"Story {story_id} not found")
                return None
            return data
        except Exception as e:
            logger.error(f"Failed to fetch story {story_id}: {e}")
            return None
