# src/agent/tools.py
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Tool(ABC):
    """工具基类，所有工具必须继承此类"""

    def __init__(self, name: str, description: str, parameters: dict):
        self.name = name
        self.description = description
        self.parameters = parameters

    @abstractmethod
    def execute(self, **kwargs) -> dict:
        """执行工具，返回结果字典"""
        pass

    def to_dict(self) -> dict:
        """转换为字典格式（供 LLM 选择）"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class ToolRegistry:
    """工具注册表，管理所有可用工具"""

    def __init__(self):
        self.tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get(self, name: str) -> Tool | None:
        """获取工具"""
        return self.tools.get(name)

    def list_tools(self) -> list[dict]:
        """列出所有工具（供 LLM 选择）"""
        return [tool.to_dict() for tool in self.tools.values()]

    def has_tool(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self.tools
