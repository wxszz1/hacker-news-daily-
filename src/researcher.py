import logging
from src.models import Story

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个技术研究员。请根据提供的文章信息，生成一份简短但有深度的研究报告。

报告要求：
1. 使用中文撰写
2. 解释这项技术/进展的核心意义
3. 分析可能的影响和应用场景
4. 提出值得关注的后续方向
5. 控制在500字以内"""

USER_PROMPT_TEMPLATE = """请为以下高价值文章生成研究报告：

标题：{title}
Hacker News 点赞数：{score}（说明社区认可度高）
摘要：{summary}
链接：{url}

请返回JSON格式：{{"report": "研究报告内容", "highlights": ["亮点1", "亮点2", ...]}}"""


class Researcher:
    """对高分文章进行深度研究"""

    def __init__(self, llm_client, config):
        self.llm = llm_client
        self.score_threshold = config.score_threshold
        self.max_research_length = config.max_research_length
        self.enabled = llm_client.enabled and config.enabled

    def research(self, story: Story) -> dict:
        """对单篇高分文章生成研究报告"""
        if not self.enabled or not story.title:
            return {"report": "", "highlights": []}

        user_prompt = USER_PROMPT_TEMPLATE.format(
            title=story.title,
            score=story.agent_score,
            summary=story.summary or "（无摘要）",
            url=story.url
        )

        result = self.llm.chat_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=800
        )

        if result:
            return {
                "report": result.get("report", ""),
                "highlights": result.get("highlights", [])
            }

        return {"report": "", "highlights": []}

    def research_batch(self, stories: list[Story]) -> list[dict]:
        """批量研究（仅处理高分文章）"""
        if not self.enabled:
            return [{"report": "", "highlights": []} for _ in stories]

        results = []
        for story in stories:
            if story.agent_score >= self.score_threshold:
                result = self.research(story)
                results.append(result)
            else:
                results.append({"report": "", "highlights": []})

        return results
