# src/agent/planner.py
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个任务规划专家。根据用户任务和可用工具，制定执行计划。

规划原则：
1. 每个步骤只使用一个工具
2. 步骤之间要有逻辑顺序
3. 根据任务复杂度决定步骤数量（通常3-6步）
4. 确保每一步都有明确的目的"""

USER_PROMPT_TEMPLATE = """任务：{task}

可用工具：
{tools_desc}

请制定执行计划，返回 JSON 格式：
{{
    "steps": [
        {{
            "step_id": 1,
            "tool": "工具名称",
            "input": {{"参数": "值"}},
            "purpose": "这一步的目的"
        }}
    ],
    "reasoning": "选择这些步骤的原因"
}}

注意：
1. tool 必须是上面列出的工具名称之一
2. input 的参数必须符合工具的参数定义
3. 步骤之间要有逻辑依赖关系"""


class Planner:
    """规划模块 - Agent 自主制定执行计划"""

    def __init__(self, llm_client):
        self.llm = llm_client

    def create_plan(self, task: str, available_tools: list[dict]) -> dict | None:
        """
        制定执行计划

        Args:
            task: 用户任务描述
            available_tools: 可用工具列表

        Returns:
            包含 steps 和 reasoning 的字典，失败返回 None
        """
        if not task:
            logger.warning("Empty task, cannot create plan")
            return None

        # 构造工具描述
        tools_desc = "\n".join([
            f"- {t['name']}: {t['description']}"
            for t in available_tools
        ])

        user_prompt = USER_PROMPT_TEMPLATE.format(
            task=task,
            tools_desc=tools_desc
        )

        result = self.llm.chat_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=800
        )

        if result and "steps" in result:
            # 验证计划
            validated_plan = self._validate_plan(result, available_tools)
            return validated_plan

        logger.warning(f"Failed to create plan for task: {task}")
        return None

    def _validate_plan(self, plan: dict, available_tools: list[dict]) -> dict:
        """验证计划的有效性"""
        tool_names = {t["name"] for t in available_tools}
        valid_steps = []

        for step in plan.get("steps", []):
            # 验证工具是否存在
            if step.get("tool") not in tool_names:
                logger.warning(f"Invalid tool: {step.get('tool')}, skipping step")
                continue

            # 确保 step_id 存在
            if "step_id" not in step:
                step["step_id"] = len(valid_steps) + 1

            valid_steps.append(step)

        plan["steps"] = valid_steps
        return plan
