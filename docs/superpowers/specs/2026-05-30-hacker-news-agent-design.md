# Hacker News Agent 设计文档

## 项目概述

一个自动爬取 Hacker News 专项新闻并推送到微信的工具，帮助软件工程学生获取 Agent 开发方向的有价值信息。

## 技术选型

- **语言**: Python 3.11+
- **HTTP 客户端**: httpx (支持异步)
- **配置管理**: PyYAML + Pydantic (配置校验)
- **数据库**: SQLite (轻量级，无需额外服务)
- **调度器**: APScheduler (定时任务)
- **推送服务**: Server酱 (微信推送)
- **部署**: Docker / systemd

## 架构设计

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    scheduler (调度器)                     │
│               每天 08:00 触发，协调各模块                   │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   scraper    │───▶│   filter     │───▶│  formatter   │
│   爬虫模块    │    │   过滤模块    │    │   格式化模块   │
└──────────────┘    └──────────────┘    └──────────────┘
        │                  │                    │
        │                  ▼                    ▼
        │           ┌──────────────┐    ┌──────────────┐
        │           │  config.yaml │    │   notifier   │
        │           │  配置文件     │    │  推送模块     │
        │           └──────────────┘    └──────────────┘
        │                                      │
        ▼                                      ▼
┌──────────────┐                     ┌──────────────┐
│   SQLite     │                     │   Server酱   │
│  状态存储     │                     │   微信推送    │
└──────────────┘                     └──────────────┘
        │
        ▼
┌──────────────┐
│   logging    │
│  结构化日志   │
└──────────────┘
```

### 模块职责

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| `scraper` | 从 HN API 拉取帖子 | API 端点 | 帖子列表 |
| `filter` | 按热度+关键词过滤 | 帖子列表 | 筛选后列表 |
| `formatter` | 格式化为 Markdown | 筛选后列表 | 消息内容 |
| `notifier` | 调用 Server酱推送 | 消息内容 | 推送结果 |
| `scheduler` | 定时触发 + 错误重试 | cron 配置 | 执行日志 |
| `database` | SQLite 状态存储 | 查询/写入 | 数据 |
| `health` | 健康检查 | 数据库状态 | 健康报告 |

## 数据流

```
1. scheduler 触发 run_job()
2. scraper 从 HN API 拉取 top stories
3. filter 按热度阈值 + 关键词过滤
4. formatter 格式化为 Markdown
5. notifier 调用 Server酱推送
6. database 记录已推送文章 ID
7. 失败时记录到 failed_pushes 表，下次重试
```

## 数据库设计

```sql
-- 已推送文章记录
CREATE TABLE pushed_articles (
    id INTEGER PRIMARY KEY,
    article_id INTEGER UNIQUE,
    title TEXT,
    pushed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 推送失败记录（待重试）
CREATE TABLE failed_pushes (
    id INTEGER PRIMARY KEY,
    message TEXT,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    retry_count INTEGER DEFAULT 0
);
```

## 配置文件

```yaml
hackernews:
  top_stories_limit: 30
  request_delay: 0.1

filter:
  min_score: 50
  keywords:
    - ai
    - llm
    - agent
    - langchain
    - openai
    - anthropic
    - rag
    - prompt
    - gpt
    - claude
    - python
  exclude:
    - hiring
    - ask hn: who is hiring

serverchan:
  send_key: "${SERVERCHAN_KEY}"

database:
  path: "data/hackernews.db"

logging:
  level: "INFO"
  file: "logs/app.log"
  max_bytes: 10485760
  backup_count: 5

scheduler:
  cron: "0 8 * * *"
  timezone: "Asia/Shanghai"
```

## 错误处理

1. **配置校验**: Pydantic 验证，启动时检查
2. **API 限流**: 请求间隔 100ms
3. **推送失败**: 指数退避重试 (3次)
4. **失败记录**: 存入 SQLite，下次启动时重试
5. **异常捕获**: run_job() 全局异常处理
6. **日志记录**: 结构化日志，按天轮转

## 部署方案

### 方案 A: Docker (推荐)

```bash
docker-compose up -d
```

### 方案 B: systemd

```bash
sudo systemctl enable hackernews
sudo systemctl start hackernews
```

## 项目结构

```
hacker-news-agent/
├── src/
│   ├── __init__.py
│   ├── main.py              # 入口 + 调度器
│   ├── config.py            # 配置加载与校验
│   ├── logging_config.py    # 日志配置
│   ├── scraper.py           # 爬虫模块
│   ├── filter.py            # 过滤模块
│   ├── formatter.py         # 格式化模块
│   ├── notifier.py          # 推送模块
│   ├── database.py          # 数据库模块
│   └── health.py            # 健康检查
├── config/
│   ├── config.yaml
│   └── hackernews.service
├── data/                    # 自动创建
├── logs/                    # 自动创建
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── deploy.sh
```

## 后续迭代

1. 接入 LLM 做智能摘要
2. 支持多主题订阅
3. Web UI 查看历史
4. 推送去重优化
