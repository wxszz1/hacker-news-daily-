# tests/test_agent.py
"""Agent 完整链路测试"""
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.config import load_config
from src.llm_client import LLMClient
from src.agent.core import Agent


def test_agent():
    """测试 Agent 完整链路"""
    config = load_config()
    llm_client = LLMClient(config.agent.llm)

    if not llm_client.enabled:
        print("ERROR: LLM client not enabled")
        return

    agent = Agent(
        llm_client=llm_client,
        send_key=config.serverchan.send_key
    )

    # 测试任务
    task = "搜索关于 AI Agent 的最新文章"
    print(f"Task: {task}")
    print("-" * 50)

    result = agent.run(task)
    print(f"Result: {result}")


if __name__ == "__main__":
    test_agent()
