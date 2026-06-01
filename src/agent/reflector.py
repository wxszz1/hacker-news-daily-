import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个结果评估专家。评估 Agent 执行步骤的结果质量。

评估标准：
- 9-10: 完美，超出预期
- 7-8: 良好，满足需求
- 5-6: 一般，基本可用
- 3-4: 较差，需要改进
- 1-2: 失败，需要重试"""

USER_PROMPT_TEMPLATE = """原始目标：{original_goal}

执行步骤：
{step}

执行结果：
{result}

请评估这个结果，返回 JSON：
{{
    "score": 8,
    "quality": "good",
    "feedback": "结果满足需求",
    "suggestions": ["改进建议1", "改进建议2"]
}}

quality 可选值：good / needs_improvement / failed"""


class Reflector:
    """反思模块 - 评估执行结果，决定是否需要重试"""

    def __init__(self, llm_client):
        self.llm = llm_client

    def evaluate(self, step: dict, result: dict, original_goal: str) -> dict:
        """
        评估执行结果

        Args:
            step: 执行的步骤
            result: 执行结果
            original_goal: 原始目标

        Returns:
            包含 score, quality, feedback, suggestions 的字典
        """
        user_prompt = USER_PROMPT_TEMPLATE.format(
            original_goal=original_goal,
            step=str(step),
            result=str(result)
        )

        evaluation = self.llm.chat_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=300
        )

        if evaluation:
            # 确保必要的字段存在
            evaluation.setdefault("score", 5)
            evaluation.setdefault("quality", "needs_improvement")
            evaluation.setdefault("feedback", "")
            evaluation.setdefault("suggestions", [])
            return evaluation

        # 默认评估
        return {
            "score": 5,
            "quality": "needs_improvement",
            "feedback": "评估失败，默认需要改进",
            "suggestions": []
        }

    def should_retry(self, evaluation: dict) -> bool:
        """
        决定是否需要重试

        Args:
            evaluation: 评估结果

        Returns:
            True 表示需要重试
        """
        quality = evaluation.get("quality", "failed")
        score = evaluation.get("score", 0)

        # 质量为 needs_improvement 且分数低于7时重试
        return quality == "needs_improvement" and score < 7
