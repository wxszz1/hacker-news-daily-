import httpx
import logging
from readability import Document
import re

logger = logging.getLogger(__name__)

class ContentFetcher:
    """抓取文章内容"""

    def __init__(self):
        self.timeout = 10

    def fetch(self, url: str) -> str:
        """抓取文章正文"""
        if not url:
            return ""

        try:
            resp = httpx.get(url, timeout=self.timeout, follow_redirects=True)
            if resp.status_code != 200:
                return ""

            # 用 readability 提取正文
            doc = Document(resp.text)
            text = doc.summary()

            # 清理 HTML 标签
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()

            # 截取前 1500 字符作为摘要
            if len(text) > 1500:
                text = text[:1500] + "..."

            return text
        except Exception as e:
            logger.warning(f"Failed to fetch content from {url}: {e}")
            return ""