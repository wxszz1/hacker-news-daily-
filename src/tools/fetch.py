# src/tools/fetch.py
import httpx
import logging
from src.agent.tools import Tool

logger = logging.getLogger(__name__)


class FetchTool(Tool):
    """网页抓取工具"""

    def __init__(self):
        super().__init__(
            name="fetch",
            description="抓取指定URL的网页内容",
            parameters={
                "url": {
                    "type": "string",
                    "description": "要抓取的网页URL"
                }
            }
        )

    def execute(self, url: str = "", **kwargs) -> dict:
        """执行抓取"""
        if not url:
            return {"error": "URL 不能为空"}

        try:
            resp = httpx.get(url, timeout=15, follow_redirects=True)
            resp.raise_for_status()

            # 提取文本内容（简单版本）
            content = resp.text[:5000]  # 截断过长内容

            return {
                "url": url,
                "status_code": resp.status_code,
                "content_length": len(content),
                "content": content
            }

        except Exception as e:
            logger.error(f"Fetch failed for {url}: {e}")
            return {"error": str(e), "url": url}
