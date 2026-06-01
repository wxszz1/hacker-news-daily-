from datetime import datetime
import logging
from src.translator import Translator
from src.classifier import Classifier, CATEGORIES

logger = logging.getLogger(__name__)

class MessageFormatter:
    def __init__(self, agent_enabled: bool = False):
        self.translator = Translator()
        self.classifier = Classifier()
        self.agent_enabled = agent_enabled

    def format(self, stories: list[dict]) -> str | None:
        """格式化为 Markdown 消息"""
        if not stories:
            logger.debug("No stories to format")
            return None

        logger.info("Formatting %d stories", len(stories))

        date_str = datetime.now().strftime("%Y-%m-%d")
        lines = [f"📰 Hacker News 早报 ({date_str})", ""]

        # 批量分类
        titles = [s.get("title", "Untitled") for s in stories if s and isinstance(s, dict)]
        classifications = self.classifier.classify_batch(titles) if self.classifier.enabled else []

        for i, story in enumerate(stories, 1):
            if not story or not isinstance(story, dict):
                logger.warning("Skipping malformed story at index %d: %r", i, story)
                continue

            title = story.get("title", "Untitled")
            url = story.get("url", f"https://news.ycombinator.com/item?id={story.get('id', '')}")
            score = story.get("score", 0)
            comments = story.get("descendants", 0)
            age = self._format_age(story.get("time", 0))

            # 获取分类
            category_tag = ""
            if i <= len(classifications):
                cat = classifications[i - 1]
                cat_key = cat.get("category", "other")
                category_tag = CATEGORIES.get(cat_key, "其他")

            # Agent 重要性评分
            agent_score = story.get("agent_score", 0)
            score_display = f" | 🎯 AI评分: {agent_score}/10" if agent_score else ""

            # 翻译标题
            title_cn = self.translator.translate(title)

            # 分类标签
            if category_tag:
                lines.append(f"[{category_tag}]")

            lines.append(f"{i}. {title}{score_display}")
            if self.translator.enabled and title_cn != title:
                lines.append(f"   【{title_cn}】")

            # Agent 摘要（优先使用 AI 摘要）
            summary = story.get("summary", "")
            if summary:
                lines.append(f"   📝 AI摘要: {summary}")

            # 关键要点
            key_points = story.get("key_points", [])
            if key_points:
                lines.append(f"   💡 要点:")
                for point in key_points[:3]:  # 最多显示3个要点
                    lines.append(f"      • {point}")

            lines.append(f"   👍 {score} | 💬 {comments} | 🕐 {age}")
            lines.append(f"   🔗 {url}")

            # 研究报告（仅高分文章）
            research_report = story.get("research_report", "")
            if research_report:
                lines.append(f"   📊 深度分析:")
                lines.append(f"   {research_report}")

            lines.append("")

        return "\n".join(lines)

    def _format_age(self, timestamp: int) -> str:
        delta = datetime.now().timestamp() - timestamp
        hours = int(delta // 3600)
        return f"{hours}小时前" if hours < 24 else f"{hours // 24}天前"
