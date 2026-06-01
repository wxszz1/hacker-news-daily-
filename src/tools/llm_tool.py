# src/tools/llm_tool.py
import logging
from src.agent.tools import Tool

logger = logging.getLogger(__name__)


class LLMTool(Tool):
    """LLM 分析工具"""

    def __init__(self, llm_client):
        super().__init__(
            name="llm",
            description="使用 AI 分析文本，生成摘要、分析观点等",
            parameters={
                "prompt": {
                    "type": "string",
                    "description": "分析指令，如'分析这篇文章的核心观点'"
                },
                "context": {
                    "type": "string",
                    "description": "待分析的文本内容"
                }
            }
        )
        self.llm = llm_client

    def execute(self, prompt: str = "", context: str = "", **kwargs) -> dict:
        """执行 LLM 分析"""
        if not prompt:
            return {"error": "分析指令不能为空"}

        try:
            full_prompt = f"指令：{prompt}\n\n内容：{context}"
            result = self.llm.chat(
                system_prompt="你是一个专业的技术分析师。",
                user_prompt=full_prompt
            )

            return {
                "prompt": prompt,
                "result": result or "分析失败"
            }

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {"error": str(e)}
