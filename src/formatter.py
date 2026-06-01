from datetime import datetime
import logging
from src.translator import Translator
from src.content_fetcher import ContentFetcher

logger = logging.getLogger(__name__)

class MessageFormatter:
    def __init__(self):
        self.translator = Translator()
        self.fetcher = ContentFetcher()

    def format(self, stories: list[dict]) -> str | None:
        """格式化为 Markdown 消息（中英对照，含摘要）"""
        if not stories:
            logger.debug("No stories to format")
            return None

        logger.info("Formatting %d stories", len(stories))

        date_str = datetime.now().strftime("%Y-%m-%d")
        lines = [f"📰 Hacker News 早报 ({date_str})", ""]

        for i, story in enumerate(stories, 1):
            if not story or not isinstance(story, dict):
                logger.warning("Skipping malformed story at index %d: %r", i, story)
                continue

            title = story.get("title", "Untitled")
            url = story.get("url", f"https://news.ycombinator.com/item?id={story.get('id', '')}")
            score = story.get("score", 0)
            comments = story.get("descendants", 0)
            age = self._format_age(story.get("time", 0))

            # 翻译标题
            title_cn = self.translator.translate(title)

            lines.append(f"{i}. {title}")
            if self.translator.enabled and title_cn != title:
                lines.append(f"   【{title_cn}】")

            # 抓取并翻译文章摘要
            if url and self.translator.enabled:
                content = self.fetcher.fetch(url)
                if content:
                    content_cn = self.translator.translate(content)
                    lines.append(f"   📝 摘要:")
                    lines.append(f"   {content_cn}")

            lines.append(f"   👍 {score} | 💬 {comments} | 🕐 {age}")
            lines.append(f"   🔗 {url}")
            lines.append("")

        return "\n".join(lines)

    def _format_age(self, timestamp: int) -> str:
        delta = datetime.now().timestamp() - timestamp
        hours = int(delta // 3600)
        return f"{hours}小时前" if hours < 24 else f"{hours // 24}天前"
