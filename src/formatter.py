from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MessageFormatter:
    def format(self, stories: list[dict]) -> str:
        """格式化为 Markdown 消息"""
        if not stories:
            return None

        date_str = datetime.now().strftime("%Y-%m-%d")
        lines = [f"📰 Hacker News 早报 ({date_str})", ""]

        for i, story in enumerate(stories, 1):
            title = story.get("title", "Untitled")
            url = story.get("url", f"https://news.ycombinator.com/item?id={story['id']}")
            score = story.get("score", 0)
            comments = story.get("descendants", 0)
            age = self._format_age(story.get("time", 0))

            lines.append(f"{i}. [{title}]({url})")
            lines.append(f"   👍 {score} | 💬 {comments} | 🕐 {age}")
            lines.append("")

        return "\n".join(lines)

    def _format_age(self, timestamp: int) -> str:
        delta = datetime.now().timestamp() - timestamp
        hours = int(delta // 3600)
        return f"{hours}h ago" if hours < 24 else f"{hours // 24}d ago"
