# Agent 系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现完整的 Agent 系统，包含工具系统、规划、反思、记忆四大核心组件。

**Architecture:** 采用分层架构，Agent Core 协调各组件，Tool System 封装外部能力，Planner 生成执行计划，Reflector 评估结果，Memory 存储历史。

**Tech Stack:** Python 3.11+, 智谱 GLM-4, SQLite, httpx

---

## 文件结构

```
src/
├── agent/
│   ├── __init__.py
│   ├── core.py              # Agent 核心
│   ├── tools.py             # 工具系统（Tool 基类 + ToolRegistry）
│   ├── planner.py           # 规划模块
│   ├── reflector.py         # 反思模块
│   └── memory.py            # 记忆系统
├── tools/
│   ├── __init__.py
│   ├── search.py            # 搜索工具
│   ├── fetch.py             # 抓取工具
│   ├── llm_tool.py          # LLM 工具
│   ├── translate.py         # 翻译工具
│   └── notify.py            # 通知工具
```

---

### Task 1: 创建工具系统（Tool System）

**Files:**
- Create: `src/agent/__init__.py`
- Create: `src/agent/tools.py`
- Test: `tests/test_agent_tools.py`

- [ ] **Step 1: 创建 agent 目录和 __init__.py**

```python
# src/agent/__init__.py
from src.agent.core import Agent
from src.agent.tools import Tool, ToolRegistry

__all__ = ["Agent", "Tool", "ToolRegistry"]
```

- [ ] **Step 2: 创建 tools.py - Tool 基类**

```python
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
```

- [ ] **Step 3: 运行测试验证**

```bash
cd "C:\Users\10954\Desktop\hacker-news-agent"
python -c "from src.agent.tools import Tool, ToolRegistry; print('Tool system OK')"
```

Expected: `Tool system OK`

- [ ] **Step 4: 提交**

```bash
git add src/agent/
git commit -m "feat: 添加 Agent 工具系统"
```

---

### Task 2: 创建具体工具实现

**Files:**
- Create: `src/tools/__init__.py`
- Create: `src/tools/search.py`
- Create: `src/tools/fetch.py`
- Create: `src/tools/llm_tool.py`
- Create: `src/tools/translate.py`
- Create: `src/tools/notify.py`

- [ ] **Step 1: 创建 tools 目录和 __init__.py**

```python
# src/tools/__init__.py
from src.tools.search import SearchTool
from src.tools.fetch import FetchTool
from src.tools.llm_tool import LLMTool
from src.tools.translate import TranslateTool
from src.tools.notify import NotifyTool

__all__ = ["SearchTool", "FetchTool", "LLMTool", "TranslateTool", "NotifyTool"]
```

- [ ] **Step 2: 创建 search.py - 搜索工具**

```python
# src/tools/search.py
import httpx
import logging
from src.agent.tools import Tool

logger = logging.getLogger(__name__)


class SearchTool(Tool):
    """网页搜索工具"""

    def __init__(self):
        super().__init__(
            name="search",
            description="搜索互联网获取信息，返回搜索结果列表",
            parameters={
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                }
            }
        )
        # 使用 Hacker News 搜索作为 MVP
        self.api_url = "https://hn.algolia.com/api/v1/search"

    def execute(self, query: str = "", **kwargs) -> dict:
        """执行搜索"""
        if not query:
            return {"error": "搜索关键词不能为空"}

        try:
            resp = httpx.get(
                self.api_url,
                params={"query": query, "tags": "story"},
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            # 提取前5条结果
            hits = data.get("hits", [])[:5]
            results = []
            for hit in hits:
                results.append({
                    "title": hit.get("title", ""),
                    "url": hit.get("url", ""),
                    "points": hit.get("points", 0),
                    "num_comments": hit.get("num_comments", 0),
                    "objectID": hit.get("objectID", "")
                })

            return {
                "query": query,
                "total_hits": data.get("nbHits", 0),
                "results": results
            }

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"error": str(e), "query": query}
```

- [ ] **Step 3: 创建 fetch.py - 抓取工具**

```python
# src/tools/fetch.py
import httpx
import logging
from src.agent.tools import Tool

logger = logging.getLogger(__name__)


class FetchTool(Tool):
    """网页抓取工具"""

    def __init__(self):
        super().__init__(
            name="fetch",
            description="抓取指定URL的网页内容",
            parameters={
                "url": {
                    "type": "string",
                    "description": "要抓取的网页URL"
                }
            }
        )

    def execute(self, url: str = "", **kwargs) -> dict:
        """执行抓取"""
        if not url:
            return {"error": "URL 不能为空"}

        try:
            resp = httpx.get(url, timeout=15, follow_redirects=True)
            resp.raise_for_status()

            # 提取文本内容（简单版本）
            content = resp.text[:5000]  # 截断过长内容

            return {
                "url": url,
                "status_code": resp.status_code,
                "content_length": len(content),
                "content": content
            }

        except Exception as e:
            logger.error(f"Fetch failed for {url}: {e}")
            return {"error": str(e), "url": url}
```

- [ ] **Step 4: 创建 llm_tool.py - LLM 工具**

```python
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
```

- [ ] **Step 5: 创建 translate.py - 翻译工具**

```python
# src/tools/translate.py
import os
import hashlib
import random
import httpx
import logging
from src.agent.tools import Tool

logger = logging.getLogger(__name__)


class TranslateTool(Tool):
    """翻译工具（百度翻译API）"""

    def __init__(self):
        super().__init__(
            name="translate",
            description="将英文翻译为中文",
            parameters={
                "text": {
                    "type": "string",
                    "description": "待翻译的英文文本"
                }
            }
        )
        self.app_id = os.getenv("BAIDU_FANYI_APPID", "")
        self.secret = os.getenv("BAIDU_FANYI_SECRET", "")
        self.enabled = bool(self.app_id and self.secret)

    def execute(self, text: str = "", **kwargs) -> dict:
        """执行翻译"""
        if not text:
            return {"error": "翻译文本不能为空"}

        if not self.enabled:
            return {"error": "翻译 API 未配置", "text": text}

        try:
            salt = str(random.randint(1, 65536))
            sign_str = f"{self.app_id}{text}{salt}{self.secret}"
            sign = hashlib.md5(sign_str.encode()).hexdigest()

            resp = httpx.get(
                "https://fanyi-api.baidu.com/api/trans/vip/translate",
                params={
                    "q": text,
                    "from": "en",
                    "to": "zh",
                    "appid": self.app_id,
                    "salt": salt,
                    "sign": sign
                },
                timeout=5
            )
            result = resp.json()

            if "trans_result" in result:
                translated = result["trans_result"][0]["dst"]
                return {
                    "original": text,
                    "translated": translated
                }
            else:
                return {"error": "翻译失败", "text": text}

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {"error": str(e), "text": text}
```

- [ ] **Step 6: 创建 notify.py - 通知工具**

```python
# src/tools/notify.py
import httpx
import logging
from src.agent.tools import Tool

logger = logging.getLogger(__name__)


class NotifyTool(Tool):
    """微信通知工具（Server酱）"""

    def __init__(self, send_key: str = ""):
        super().__init__(
            name="notify",
            description="通过微信发送消息通知",
            parameters={
                "title": {
                    "type": "string",
                    "description": "消息标题"
                },
                "content": {
                    "type": "string",
                    "description": "消息内容（Markdown格式）"
                }
            }
        )
        self.send_key = send_key
        self.api_url = "https://sctapi.ftqq.com/{key}.send"

    def execute(self, title: str = "", content: str = "", **kwargs) -> dict:
        """执行发送通知"""
        if not title or not content:
            return {"error": "标题和内容不能为空"}

        if not self.send_key:
            return {"error": "Server酱 SendKey 未配置"}

        try:
            resp = httpx.post(
                self.api_url.format(key=self.send_key),
                data={"title": title, "desp": content},
                timeout=10
            )
            result = resp.json()

            if resp.status_code == 200:
                return {
                    "success": True,
                    "title": title,
                    "message": "消息已发送"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "发送失败")
                }

        except Exception as e:
            logger.error(f"Notification failed: {e}")
            return {"error": str(e)}
```

- [ ] **Step 7: 提交**

```bash
git add src/tools/
git commit -m "feat: 添加 Agent 具体工具实现"
```

---

### Task 3: 创建规划模块（Planner）

**Files:**
- Create: `src/agent/planner.py`

- [ ] **Step 1: 创建 planner.py**

```python
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
```

- [ ] **Step 2: 验证模块**

```bash
cd "C:\Users\10954\Desktop\hacker-news-agent"
python -c "from src.agent.planner import Planner; print('Planner OK')"
```

Expected: `Planner OK`

- [ ] **Step 3: 提交**

```bash
git add src/agent/planner.py
git commit -m "feat: 添加 Agent 规划模块"
```

---

### Task 4: 创建反思模块（Reflector）

**Files:**
- Create: `src/agent/reflector.py`

- [ ] **Step 1: 创建 reflector.py**

```python
# src/agent/reflector.py
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
```

- [ ] **Step 2: 验证模块**

```bash
cd "C:\Users\10954\Desktop\hacker-news-agent"
python -c "from src.agent.reflector import Reflector; print('Reflector OK')"
```

Expected: `Reflector OK`

- [ ] **Step 3: 提交**

```bash
git add src/agent/reflector.py
git commit -m "feat: 添加 Agent 反思模块"
```

---

### Task 5: 创建记忆系统（Memory）

**Files:**
- Create: `src/agent/memory.py`

- [ ] **Step 1: 创建 memory.py**

```python
# src/agent/memory.py
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

import logging

logger = logging.getLogger(__name__)


class Memory:
    """记忆系统 - 存储历史信息，支持检索"""

    def __init__(self, db_path: str = "data/agent_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.short_term: list[dict] = []  # 当前任务记忆
        self._init_db()

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """初始化数据库"""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    id INTEGER PRIMARY KEY,
                    task TEXT,
                    observation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE,
                    value TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_memory_task
                ON long_term_memory(task);
            """)

    def remember(self, observation: dict):
        """存储观察（短期记忆）"""
        self.short_term.append({
            "timestamp": datetime.now().isoformat(),
            "content": observation
        })

    def save_to_long_term(self, task: str, observation: str):
        """保存到长期记忆"""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "INSERT INTO long_term_memory (task, observation) VALUES (?, ?)",
                    (task, observation)
                )
            logger.info(f"Saved to long-term memory: {task[:50]}...")
        except Exception as e:
            logger.error(f"Failed to save to long-term memory: {e}")

    def recall(self, query: str, limit: int = 5) -> list[dict]:
        """
        检索相关记忆（MVP版本使用关键词匹配）

        Args:
            query: 搜索关键词
            limit: 返回数量限制

        Returns:
            相关记忆列表
        """
        # 从短期记忆中检索
        relevant = [
            m for m in self.short_term
            if query.lower() in str(m["content"]).lower()
        ]

        # 如果短期记忆不够，从长期记忆中检索
        if len(relevant) < limit:
            try:
                with self.get_connection() as conn:
                    rows = conn.execute(
                        "SELECT task, observation, created_at FROM long_term_memory "
                        "WHERE task LIKE ? OR observation LIKE ? "
                        "ORDER BY created_at DESC LIMIT ?",
                        (f"%{query}%", f"%{query}%", limit)
                    ).fetchall()

                    for task, observation, created_at in rows:
                        relevant.append({
                            "timestamp": created_at,
                            "content": {"task": task, "observation": observation}
                        })
            except Exception as e:
                logger.error(f"Failed to recall from long-term memory: {e}")

        return relevant[-limit:]

    def save_user_preference(self, key: str, value: str):
        """保存用户偏好"""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO user_preferences (key, value) VALUES (?, ?)",
                    (key, value)
                )
            logger.info(f"Saved user preference: {key}={value}")
        except Exception as e:
            logger.error(f"Failed to save user preference: {e}")

    def get_user_preference(self, key: str) -> str:
        """获取用户偏好"""
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    "SELECT value FROM user_preferences WHERE key = ?",
                    (key,)
                ).fetchone()
                return row[0] if row else ""
        except Exception as e:
            logger.error(f"Failed to get user preference: {e}")
            return ""

    def clear_short_term(self):
        """清空短期记忆"""
        self.short_term.clear()
```

- [ ] **Step 2: 验证模块**

```bash
cd "C:\Users\10954\Desktop\hacker-news-agent"
python -c "from src.agent.memory import Memory; m = Memory(); print('Memory OK')"
```

Expected: `Memory OK`

- [ ] **Step 3: 提交**

```bash
git add src/agent/memory.py
git commit -m "feat: 添加 Agent 记忆系统"
```

---

### Task 6: 创建 Agent 核心（Agent Core）

**Files:**
- Create: `src/agent/core.py`

- [ ] **Step 1: 创建 core.py**

```python
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
```

- [ ] **Step 2: 验证模块**

```bash
cd "C:\Users\10954\Desktop\hacker-news-agent"
python -c "from src.agent.core import Agent; print('Agent Core OK')"
```

Expected: `Agent Core OK`

- [ ] **Step 3: 提交**

```bash
git add src/agent/core.py
git commit -m "feat: 添加 Agent 核心模块"
```

---

### Task 7: 集成到主流程

**Files:**
- Modify: `src/main.py`

- [ ] **Step 1: 修改 main.py 添加 Agent 支持**

在 `src/main.py` 中添加 Agent 相关代码：

```python
# 在文件开头添加导入
from src.agent.core import Agent

# 添加 Agent 执行函数
def run_agent_task(user_input: str) -> str:
    """执行 Agent 任务"""
    load_dotenv()
    config = load_config()

    # 创建 LLM 客户端
    from src.llm_client import LLMClient
    llm_client = LLMClient(config.agent.llm)

    if not llm_client.enabled:
        return "Agent 未启用，请配置 ZHIPU_API_KEY"

    # 创建 Agent
    agent = Agent(
        llm_client=llm_client,
        send_key=config.serverchan.send_key
    )

    # 执行任务
    return agent.run(user_input)
```

- [ ] **Step 2: 验证集成**

```bash
cd "C:\Users\10954\Desktop\hacker-news-agent"
python -c "from src.main import run_agent_task; print('Integration OK')"
```

Expected: `Integration OK`

- [ ] **Step 3: 提交**

```bash
git add src/main.py
git commit -m "feat: 集成 Agent 到主流程"
```

---

### Task 8: 测试完整链路

**Files:**
- Create: `tests/test_agent.py`

- [ ] **Step 1: 创建测试脚本**

```python
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
```

- [ ] **Step 2: 运行测试**

```bash
cd "C:\Users\10954\Desktop\hacker-news-agent"
python tests/test_agent.py
```

Expected: Agent 完整执行，返回搜索结果

- [ ] **Step 3: 提交**

```bash
git add tests/test_agent.py
git commit -m "test: 添加 Agent 完整链路测试"
```

---

### Task 9: 部署到服务器

- [ ] **Step 1: 推送到 GitHub**

```bash
cd "C:\Users\10954\Desktop\hacker-news-agent"
git push
```

- [ ] **Step 2: 服务器拉取代码**

```bash
ssh -i "C:\Users\10954\.ssh\id_ed25519" admin@47.109.80.101 "cd ~/hacker-news-agent && git pull && sudo systemctl restart hackernews"
```

- [ ] **Step 3: 验证服务状态**

```bash
ssh -i "C:\Users\10954\.ssh\id_ed25519" admin@47.109.80.101 "sudo systemctl status hackernews --no-pager"
```

Expected: 服务正常运行

---

## 完整链路验证

```
用户微信消息: "研究一下 AI Agent 的最新进展"
    │
    ▼
Agent._understand_intent()
    → "用户想了解 AI Agent 的最新进展"
    │
    ▼
Agent.planner.create_plan()
    → 步骤1: search("AI Agent 最新进展")
    → 步骤2: fetch(搜索结果URL)
    → 步骤3: llm(分析文章)
    → 步骤4: notify(发送报告)
    │
    ▼
Agent._execute_step() × 4
    → 调用 SearchTool / FetchTool / LLMTool / NotifyTool
    │
    ▼
Agent.reflector.evaluate() × 4
    → 评估每一步的质量
    │
    ▼
Agent.memory.remember() × 4
    → 记录执行过程
    │
    ▼
Agent._generate_response()
    → 生成最终回复
    │
    ▼
返回微信消息
```
