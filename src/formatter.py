from datetime import datetime
import logging
from src.translator import Translator
from src.classifier import Classifier, CATEGORIES
from src.models import Story

logger = logging.getLogger(__name__)

# 消息最大长度（Server酱限制）
MAX_MESSAGE_LENGTH = 8000


class MessageFormatter:
    def __init__(self, llm_client=None, db=None):
        self.translator = Translator(db)
        self.classifier = Classifier(llm_client, db)

    def format(self, stories: list[Story]) -> str | None:
        """格式化为 Markdown 消息"""
        if not stories:
            logger.debug("No stories to format")
            return None

        logger.info("Formatting %d stories", len(stories))

        date_str = datetime.now().strftime("%Y-%m-%d")
        lines = [f"📰 Hacker News 早报 ({date_str})", ""]

        for i, story in enumerate(stories, 1):
            if not story or not isinstance(story, Story):
                logger.warning("Skipping malformed story at index %d: %r", i, story)
                continue

            # 分类标签
            if story.category:
                lines.append(f"[{story.category}]")

            # 标题 + AI 评分
            score_display = f" | 🎯 AI评分: {story.agent_score}/10" if story.agent_score else ""
            lines.append(f"{i}. {story.title}{score_display}")

            # 中文翻译
            if story.title_cn:
                lines.append(f"   【{story.title_cn}】")

            # AI 摘要
            if story.summary:
                lines.append(f"   📝 AI摘要: {story.summary}")

            # 关键要点
            if story.key_points:
                lines.append(f"   💡 要点:")
                for point in story.key_points[:3]:
                    lines.append(f"      • {point}")

            lines.append(f"   👍 {story.score} | 💬 {story.descendants} | 🕐 {self._format_age(story.time)}")
            lines.append(f"   🔗 {story.url}")

            # 研究报告（仅高分文章）
            if story.research_report:
                lines.append(f"   📊 深度分析:")
                lines.append(f"   {story.research_report}")

            lines.append("")

        message = "\n".join(lines)

        # 消息长度控制
        if len(message) > MAX_MESSAGE_LENGTH:
            message = self._truncate_message(stories, date_str)

        return message

    def _truncate_message(self, stories: list[Story], date_str: str) -> str:
        """截断过长的消息，只保留标题和评分"""
        lines = [f"📰 Hacker News 早报 ({date_str})", ""]

        for i, story in enumerate(stories, 1):
            if not story or not isinstance(story, Story):
                continue

            score_display = f" | 🎯{story.agent_score}" if story.agent_score else ""
            lines.append(f"{i}. {story.title}{score_display}")
            lines.append(f"   👍 {story.score} | 💬 {story.descendants}")
            lines.append(f"   🔗 {story.url}")
            lines.append("")

            # 保留前5条的完整内容
            if i >= 5:
                lines.append(f"... 还有 {len(stories) - 5} 条，详见完整版")
                break

        return "\n".join(lines)

    def _format_age(self, timestamp: int) -> str:
        delta = datetime.now().timestamp() - timestamp
        hours = int(delta // 3600)
        return f"{hours}小时前" if hours < 24 else f"{hours // 24}天前"
