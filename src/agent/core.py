# src/agent/core.py
import json
import logging

from src.agent.tools import ToolRegistry
from src.agent.planner import Planner
from src.agent.reflector import Reflector
from src.agent.memory import Memory

logger = logging.getLogger(__name__)


class Agent:
    """
    Agent 核心 - 协调各组件，执行任务

    完整链路：用户消息 → 意图理解 → 规划 → 执行 → 反思 → 记忆 → 生成回复
    """

    def __init__(self, llm_client, send_key: str = "", db_path: str = "data/agent_memory.db"):
        self.llm = llm_client
        self.tools = ToolRegistry()
        self.planner = Planner(llm_client)
        self.reflector = Reflector(llm_client)
        self.memory = Memory(db_path)
        self.send_key = send_key

        # 注册默认工具
        self._register_default_tools()

    def _register_default_tools(self):
        """注册默认工具"""
        from src.tools.search import SearchTool
        from src.tools.fetch import FetchTool
        from src.tools.llm_tool import LLMTool
        from src.tools.translate import TranslateTool
        from src.tools.notify import NotifyTool

        self.tools.register(SearchTool())
        self.tools.register(FetchTool())
        self.tools.register(LLMTool(self.llm))
        self.tools.register(TranslateTool())
        self.tools.register(NotifyTool(self.send_key))

    def run(self, user_input: str) -> str:
        """
        Agent 主循环

        Args:
            user_input: 用户输入

        Returns:
            Agent 的回复
        """
        logger.info(f"Agent received: {user_input}")

        try:
            # 1. 理解意图
            intent = self._understand_intent(user_input)
            logger.info(f"Intent: {intent}")

            # 2. 制定计划
            available_tools = self.tools.list_tools()
            plan = self.planner.create_plan(intent, available_tools)

            if not plan or "steps" not in plan:
                return "抱歉，我无法制定执行计划。请尝试更具体的描述。"

            logger.info(f"Plan created with {len(plan['steps'])} steps")

            # 3. 执行计划
            results = []
            for step in plan["steps"]:
                # 执行步骤
                result = self._execute_step(step)
                logger.info(f"Step {step.get('step_id')}: {step.get('tool')} -> {result.get('success', 'done')}")

                # 反思结果
                evaluation = self.reflector.evaluate(step, result, intent)
                logger.info(f"Evaluation: score={evaluation.get('score')}, quality={evaluation.get('quality')}")

                # 决定是否重试
                if self.reflector.should_retry(evaluation):
                    logger.info("Retrying step with feedback...")
                    result = self._retry_with_feedback(step, evaluation)

                # 记忆
                self.memory.remember({
                    "step": step,
                    "result": result,
                    "evaluation": evaluation
                })

                results.append(result)

            # 4. 生成最终回复
            final_response = self._generate_response(results, user_input)

            # 5. 保存到长期记忆
            self.memory.save_to_long_term(user_input, final_response)

            return final_response

        except Exception as e:
            logger.exception(f"Agent error: {e}")
            return f"抱歉，处理过程中出现错误：{str(e)}"

    def _understand_intent(self, user_input: str) -> str:
        """理解用户意图"""
        prompt = f"""用户说：{user_input}

请分析用户的真实意图，用一句话描述。
例如："用户想了解 AI Agent 的最新进展"
例如："用户想搜索关于 Python 的教程"
例如："用户想翻译一段英文文本" """

        return self.llm.chat(
            system_prompt="你是一个意图分析专家。",
            user_prompt=prompt
        )

    def _execute_step(self, step: dict) -> dict:
        """执行单个步骤"""
        tool_name = step.get("tool")
        tool_input = step.get("input", {})

        tool = self.tools.get(tool_name)
        if not tool:
            return {"error": f"工具 {tool_name} 不存在"}

        try:
            return tool.execute(**tool_input)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"error": str(e)}

    def _retry_with_feedback(self, step: dict, evaluation: dict) -> dict:
        """根据反馈重试"""
        # 将改进建议添加到输入中
        enhanced_step = step.copy()
        enhanced_step["improvement_suggestions"] = evaluation.get("suggestions", [])

        return self._execute_step(enhanced_step)

    def _generate_response(self, results: list, user_input: str) -> str:
        """生成最终回复"""
        # 整理结果
        results_summary = []
        for i, r in enumerate(results, 1):
            if "error" in r:
                results_summary.append(f"步骤{i}: 失败 - {r['error']}")
            else:
                # 提取关键信息
                if "result" in r:
                    results_summary.append(f"步骤{i}: {r['result'][:200]}")
                elif "results" in r:
                    results_summary.append(f"步骤{i}: 找到{len(r['results'])}条结果")
                elif "translated" in r:
                    results_summary.append(f"步骤{i}: {r['translated']}")
                else:
                    results_summary.append(f"步骤{i}: 完成")

        prompt = f"""用户问题：{user_input}

执行结果：
{chr(10).join(results_summary)}

请生成简洁、有价值的回复。
回复要：
1. 直接回答用户问题
2. 包含关键信息
3. 使用中文
4. 适当使用 Markdown 格式"""

        return self.llm.chat(
            system_prompt="你是一个友好的AI助手。",
            user_prompt=prompt
        )
