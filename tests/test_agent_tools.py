# tests/test_agent_tools.py
import pytest
from src.agent.tools import Tool, ToolRegistry


class MockTool(Tool):
    """用于测试的模拟工具"""

    def __init__(self):
        super().__init__(
            name="mock_tool",
            description="A mock tool for testing",
            parameters={"param1": {"type": "string", "description": "Test param"}}
        )

    def execute(self, **kwargs) -> dict:
        return {"status": "success", "result": kwargs.get("param1", "default")}


class TestTool:
    """测试 Tool 基类"""

    def test_tool_initialization(self):
        tool = MockTool()
        assert tool.name == "mock_tool"
        assert tool.description == "A mock tool for testing"
        assert "param1" in tool.parameters

    def test_tool_to_dict(self):
        tool = MockTool()
        result = tool.to_dict()
        assert result["name"] == "mock_tool"
        assert result["description"] == "A mock tool for testing"
        assert "parameters" in result

    def test_tool_execute(self):
        tool = MockTool()
        result = tool.execute(param1="test_value")
        assert result["status"] == "success"
        assert result["result"] == "test_value"


class TestToolRegistry:
    """测试 ToolRegistry"""

    def test_register_tool(self):
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        assert registry.has_tool("mock_tool")

    def test_get_tool(self):
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        retrieved = registry.get("mock_tool")
        assert retrieved is tool

    def test_get_nonexistent_tool(self):
        registry = ToolRegistry()
        result = registry.get("nonexistent")
        assert result is None

    def test_has_tool(self):
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        assert registry.has_tool("mock_tool") is True
        assert registry.has_tool("other_tool") is False

    def test_list_tools(self):
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        tools_list = registry.list_tools()
        assert len(tools_list) == 1
        assert tools_list[0]["name"] == "mock_tool"
