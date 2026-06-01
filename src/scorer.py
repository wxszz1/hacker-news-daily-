import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个技术文章重要性评估专家。请根据文章标题和Hacker News的点赞数，评估文章的重要性。

评分标准（1-10分）：
- 9-10: 颠覆性技术突破、重大行业事件
- 7-8: 重要技术进展、值得关注的趋势
- 5-6: 一般技术讨论、有一定价值
- 3-4: 普通内容、价值有限
- 1-2: 低价值内容

考虑因素：
1. 技术影响力和创新程度
2. 对AI/LLM/Agent领域的相关性
3. 实用性和可操作性
4. 社区关注度（点赞数参考）"""

USER_PROMPT_TEMPLATE = """请评估以下文章的重要性：

标题：{title}
Hacker News 点赞数：{score}
链接：{url}

请返回JSON格式：{{"importance": 8, "reason": "评分理由简述"}}"""


class Scorer:
    """使用 LLM 评估文章重要性"""

    def __init__(self, llm_client, config):
        self.llm = llm_client
        self.threshold = config.threshold
        self.enabled = llm_client.enabled and config.enabled

    def score(self, title: str, hn_score: int, url: str) -> dict:
        """评估单篇文章重要性"""
        if not self.enabled or not title:
            return {"importance": 5, "reason": "评分未启用"}

        user_prompt = USER_PROMPT_TEMPLATE.format(
            title=title,
            score=hn_score,
            url=url
        )

        result = self.llm.chat_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=200
        )

        if result:
            importance = result.get("importance", 5)
            # 确保在 1-10 范围内
            importance = max(1, min(10, int(importance)))
            return {
                "importance": importance,
                "reason": result.get("reason", "")
            }

        return {"importance": 5, "reason": "评分失败"}

    def score_batch(self, stories: list[dict]) -> list[dict]:
        """批量评分"""
        if not self.enabled:
            return [{"importance": 5, "reason": "评分未启用"} for _ in stories]

        results = []
        for story in stories:
            result = self.score(
                title=story.get("title", ""),
                hn_score=story.get("score", 0),
                url=story.get("url", "")
            )
            results.append(result)

        return results

    def filter_by_threshold(self, stories: list[dict], scores: list[dict]) -> list[tuple[dict, dict]]:
        """根据阈值过滤文章"""
        filtered = []
        for story, score_info in zip(stories, scores):
            if score_info["importance"] >= self.threshold:
                filtered.append((story, score_info))
        return filtered
