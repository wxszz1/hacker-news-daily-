# Hacker News Agent - 真正的 Agent 系统设计

> **目标：** 构建一个可交互的深度研究助手，展示 Agent 开发能力，用于求职面试。

---

## 1. 架构概览

```
┌─────────────────────────────────────────────────┐
│              Agent Core（决策大脑）               │
│         理解意图 → 制定计划 → 执行 → 反思         │
└─────────────────────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
       ▼               ▼               ▼
   ┌───────┐       ┌───────┐       ┌───────┐
   │ Tools │       │Memory │       │ Plan  │
   │ 工具  │       │ 记忆  │       │ 规划  │
   └───────┘       └───────┘       └───────┘
```

**核心理念：**
- LLM 是"大脑"，负责决策
- 工具是"手脚"，负责执行
- 记忆是"经验"，负责学习
- 规划是"蓝图"，负责步骤
- 反思是"复盘"，负责改进

---

## 2. 组件设计

### 2.1 工具系统（Tool System）

**职责：** 封装外部能力，供 Agent 调用

```python
# 工具注册表
class ToolRegistry:
    def __init__(self):
        self.tools = {}
    
    def register(self, name: str, tool):
        """注册工具"""
        self.tools[name] = tool
    
    def get(self, name: str):
        """获取工具"""
        return self.tools.get(name)
    
    def list_tools(self) -> list:
        """列出所有工具（供 LLM 选择）"""
        return [
            {
                "name": name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for name, tool in self.tools.items()
        ]

# 工具基类
class Tool:
    def __init__(self, name: str, description: str, parameters: dict):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    def execute(self, **kwargs) -> dict:
        """执行工具"""
        raise NotImplementedError
```

**MVP 工具列表：**

| 工具 | 功能 | 参数 |
|------|------|------|
| `search` | 网页搜索 | `query: str` |
| `fetch` | 抓取网页 | `url: str` |
| `llm` | AI 分析 | `prompt: str, context: str` |
| `translate` | 翻译 | `text: str` |
| `notify` | 发送通知 | `title: str, content: str` |

**工具调用格式（供 LLM 输出）：**
```json
{
    "tool": "search",
    "input": {"query": "AI Agent 最新进展"},
    "reason": "需要搜索相关信息"
}
```

---

### 2.2 规划模块（Planning）

**职责：** Agent 自主制定执行计划

```python
class Planner:
    def __init__(self, llm):
        self.llm = llm
    
    def create_plan(self, task: str, available_tools: list) -> list:
        """
        制定执行计划
        
        输入: 用户任务 + 可用工具列表
        输出: 步骤列表
        """
        tools_desc = "\n".join([
            f"- {t['name']}: {t['description']}"
            for t in available_tools
        ])
        
        prompt = f"""
        任务：{task}
        
        可用工具：
        {tools_desc}
        
        请制定执行计划，返回 JSON：
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
        1. 每个步骤只使用一个工具
        2. 步骤之间要有逻辑顺序
        3. 根据任务复杂度决定步骤数量
        """
        
        return self.llm.chat_json(prompt)
```

**规划示例：**
```
用户: "研究一下 AI Agent 的最新进展"

Agent 输出:
{
    "steps": [
        {
            "step_id": 1,
            "tool": "search",
            "input": {"query": "AI Agent 2024 最新进展"},
            "purpose": "搜索相关文章"
        },
        {
            "step_id": 2,
            "tool": "fetch",
            "input": {"url": "从搜索结果中选择"},
            "purpose": "抓取文章内容"
        },
        {
            "step_id": 3,
            "tool": "llm",
            "input": {"prompt": "分析文章核心观点", "context": "文章内容"},
            "purpose": "分析文章"
        },
        {
            "step_id": 4,
            "tool": "notify",
            "input": {"title": "AI Agent 研究报告", "content": "分析结果"},
            "purpose": "发送报告"
        }
    ],
    "reasoning": "先搜索获取信息，再抓取详情，然后分析，最后发送"
}
```

---

### 2.3 反思模块（Reflection）

**职责：** 评估执行结果，决定是否需要重试

```python
class Reflector:
    def __init__(self, llm):
        self.llm = llm
    
    def evaluate(self, step: dict, result: dict, original_goal: str) -> dict:
        """
        评估执行结果
        
        返回:
        - score: 1-10 分
        - quality: "good" / "needs_improvement" / "failed"
        - feedback: 具体反馈
        - suggestions: 改进建议
        """
        prompt = f"""
        原始目标：{original_goal}
        执行步骤：{step}
        执行结果：{result}
        
        请评估这个结果：
        {{
            "score": 8,
            "quality": "good",
            "feedback": "结果满足需求",
            "suggestions": []
        }}
        
        评分标准：
        - 9-10: 完美，超出预期
        - 7-8: 良好，满足需求
        - 5-6: 一般，基本可用
        - 3-4: 较差，需要改进
        - 1-2: 失败，需要重试
        """
        
        return self.llm.chat_json(prompt)
    
    def should_retry(self, evaluation: dict) -> bool:
        """决定是否需要重试"""
        return evaluation.get("quality") == "needs_improvement" and evaluation.get("score", 0) < 7
```

---

### 2.4 记忆系统（Memory）

**职责：** 存储历史信息，支持检索

```python
class Memory:
    def __init__(self, db_path: str = "data/agent_memory.db"):
        self.db_path = db_path
        self.short_term = []  # 当前任务记忆
        self._init_db()
    
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
            """)
    
    def remember(self, observation: dict):
        """存储观察（短期记忆）"""
        self.short_term.append({
            "timestamp": datetime.now(),
            "content": observation
        })
    
    def save_to_long_term(self, task: str, observation: str):
        """保存到长期记忆"""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO long_term_memory (task, observation) VALUES (?, ?)",
                (task, observation)
            )
    
    def recall(self, query: str, limit: int = 5) -> list:
        """检索相关记忆"""
        # 简单关键词匹配（MVP 版本）
        relevant = [
            m for m in self.short_term
            if query.lower() in str(m["content"]).lower()
        ]
        return relevant[-limit:]
    
    def save_user_preference(self, key: str, value: str):
        """保存用户偏好"""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_preferences (key, value) VALUES (?, ?)",
                (key, value)
            )
    
    def get_user_preference(self, key: str) -> str:
        """获取用户偏好"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM user_preferences WHERE key = ?",
                (key,)
            ).fetchone()
            return row[0] if row else ""
```

---

### 2.5 Agent 核心（Agent Core）

**职责：** 协调各组件，执行任务

```python
class Agent:
    def __init__(self, llm_client, db_path: str = "data/agent_memory.db"):
        self.llm = llm_client
        self.tools = ToolRegistry()
        self.planner = Planner(llm_client)
        self.reflector = Reflector(llm_client)
        self.memory = Memory(db_path)
        
        # 注册默认工具
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        self.tools.register("search", SearchTool())
        self.tools.register("fetch", FetchTool())
        self.tools.register("llm", LLMTool(self.llm))
        self.tools.register("translate", TranslateTool())
        self.tools.register("notify", NotifyTool())
    
    def run(self, user_input: str) -> str:
        """
        Agent 主循环
        
        1. 理解用户意图
        2. 制定计划
        3. 执行计划（带反思）
        4. 返回结果
        """
        # 1. 理解意图
        intent = self._understand_intent(user_input)
        
        # 2. 制定计划
        available_tools = self.tools.list_tools()
        plan = self.planner.create_plan(intent, available_tools)
        
        if not plan or "steps" not in plan:
            return "抱歉，我无法制定执行计划。"
        
        # 3. 执行计划
        results = []
        for step in plan["steps"]:
            # 执行步骤
            result = self._execute_step(step)
            
            # 反思结果
            evaluation = self.reflector.evaluate(step, result, intent)
            
            # 决定是否重试
            if self.reflector.should_retry(evaluation):
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
    
    def _understand_intent(self, user_input: str) -> str:
        """理解用户意图"""
        prompt = f"""
        用户说：{user_input}
        
        请分析用户的真实意图，用一句话描述。
        例如："用户想了解 AI Agent 的最新进展"
        """
        return self.llm.chat(prompt)
    
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
            return {"error": str(e)}
    
    def _retry_with_feedback(self, step: dict, evaluation: dict) -> dict:
        """根据反馈重试"""
        # 在 prompt 中加入改进意见
        enhanced_step = step.copy()
        enhanced_step["improvement_suggestions"] = evaluation.get("suggestions", [])
        
        return self._execute_step(enhanced_step)
    
    def _generate_response(self, results: list, user_input: str) -> str:
        """生成最终回复"""
        prompt = f"""
        用户问题：{user_input}
        
        执行结果：
        {json.dumps(results, ensure_ascii=False, indent=2)}
        
        请生成简洁、有价值的回复。
        回复要：
        1. 直接回答用户问题
        2. 包含关键信息
        3. 结构清晰
        """
        return self.llm.chat(prompt)
```

---

## 3. 数据流

```
用户微信消息
    │
    ▼
Agent.run(user_input)
    │
    ├→ _understand_intent()          # 理解意图（1次LLM）
    │
    ├→ planner.create_plan()         # 制定计划（1次LLM）
    │
    ├→ for step in plan["steps"]:    # 执行每个步骤
    │   │
    │   ├→ _execute_step()           # 执行工具
    │   │   └→ tool.execute()        # 调用外部工具
    │   │
    │   ├→ reflector.evaluate()      # 反思（1次LLM/步骤）
    │   │
    │   └→ memory.remember()         # 记忆
    │
    └→ _generate_response()          # 生成回复（1次LLM）
    │
    ▼
返回微信消息
```

**LLM 调用次数：** 3 + N（N=步骤数）

---

## 4. 文件结构

```
src/
├── agent/
│   ├── __init__.py
│   ├── core.py              # Agent 核心
│   ├── tools.py             # 工具系统
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
└── ...
```

---

## 5. 完整 Agent 链路（必须实现）

**目标：** 保整完整的 Agent 链路，确保所有核心组件都实现。

| 优先级 | 组件 | 工作量 | 面试价值 | 必须 |
|--------|------|--------|----------|------|
| **P0** | Agent 核心循环 | 2小时 | ⭐⭐⭐⭐⭐ | ✅ |
| **P0** | 工具系统 | 2小时 | ⭐⭐⭐⭐⭐ | ✅ |
| **P0** | 规划模块 | 1小时 | ⭐⭐⭐⭐ | ✅ |
| **P0** | 反思模块 | 1小时 | ⭐⭐⭐ | ✅ |
| **P0** | 记忆系统 | 2小时 | ⭐⭐⭐ | ✅ |

**完整链路：**
```
用户消息 → 意图理解 → 规划 → 执行(工具调用×N) → 反思 → 记忆 → 生成回复
```

---

## 6. 面试亮点

**面试时要能讲清楚：**

1. **架构设计**
   - 为什么选择这种分层架构
   - 各组件的职责和交互

2. **工具系统**
   - 如何设计可扩展的工具注册
   - 工具调用的格式和流程

3. **规划能力**
   - LLM 如何生成执行计划
   - 计划的结构和验证

4. **反思机制**
   - 如何评估执行结果
   - 如何决定是否重试

5. **记忆系统**
   - 短期记忆 vs 长期记忆
   - 如何检索相关记忆

---

## 7. 技术栈

- **语言：** Python 3.11+
- **LLM：** 智谱 GLM-4（glm-4-flash，免费）
- **数据库：** SQLite
- **HTTP：** httpx
- **推送：** Server酱（微信）

---

## 8. 验证方式

1. **功能验证**
   - 用户通过微信发送"研究一下 AI Agent"
   - Agent 自动搜索、分析、生成报告
   - 报告推送到微信

2. **面试演示**
   - 展示 Agent 的规划过程
   - 展示工具调用日志
   - 展示反思和改进过程
