# src/tools/search.py
import httpx
import logging
from src.agent.tools import Tool

logger = logging.getLogger(__name__)


class SearchTool(Tool):
    """网页搜索工具"""

    def __init__(self):
        super().__init__(
            name="search",
            description="搜索互联网获取信息，返回搜索结果列表",
            parameters={
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                }
            }
        )
        # 使用 Hacker News 搜索作为 MVP
        self.api_url = "https://hn.algolia.com/api/v1/search"

    def execute(self, query: str = "", **kwargs) -> dict:
        """执行搜索"""
        if not query:
            return {"error": "搜索关键词不能为空"}

        try:
            resp = httpx.get(
                self.api_url,
                params={"query": query, "tags": "story"},
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            # 提取前5条结果
            hits = data.get("hits", [])[:5]
            results = []
            for hit in hits:
                results.append({
                    "title": hit.get("title", ""),
                    "url": hit.get("url", ""),
                    "points": hit.get("points", 0),
                    "num_comments": hit.get("num_comments", 0),
                    "objectID": hit.get("objectID", "")
                })

            return {
                "query": query,
                "total_hits": data.get("nbHits", 0),
                "results": results
            }

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"error": str(e), "query": query}
