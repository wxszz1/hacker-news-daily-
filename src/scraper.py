import httpx
import time
import asyncio
import logging

logger = logging.getLogger(__name__)

class HackerNewsScraper:
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    REQUEST_DELAY = 0.1

    def __init__(self, use_async: bool = False):
        self.use_async = use_async

    def fetch_top_stories_sync(self, limit: int = 30) -> list[dict]:
        """同步获取 top stories"""
        with httpx.Client() as client:
            story_ids = self._fetch_ids_sync(client, "topstories")
            return [self._get_story_detail(client, sid) for sid in story_ids[:limit]]

    async def fetch_top_stories(self, limit: int = 30) -> list[dict]:
        """异步获取 top stories"""
        async with httpx.AsyncClient() as client:
            story_ids = await self._fetch_ids(client, "topstories")
            tasks = [self._get_story_detail(client, sid) for sid in story_ids[:limit]]
            return await asyncio.gather(*tasks)

    def _fetch_ids_sync(self, client: httpx.Client, endpoint: str) -> list[int]:
        """同步获取故事 ID 列表"""
        resp = client.get(f"{self.BASE_URL}/{endpoint}.json")
        return resp.json()

    async def _fetch_ids(self, client: httpx.AsyncClient, endpoint: str) -> list[int]:
        """异步获取故事 ID 列表"""
        resp = await client.get(f"{self.BASE_URL}/{endpoint}.json")
        return resp.json()

    def _get_story_detail(self, client: httpx.Client, story_id: int) -> dict:
        """获取单条故事详情"""
        time.sleep(self.REQUEST_DELAY)
        resp = client.get(f"{self.BASE_URL}/item/{story_id}.json")
        return resp.json()

    async def _get_story_detail(self, client: httpx.AsyncClient, story_id: int) -> dict:
        """异步获取单条故事详情"""
        await asyncio.sleep(self.REQUEST_DELAY)
        resp = await client.get(f"{self.BASE_URL}/item/{story_id}.json")
        return resp.json()
