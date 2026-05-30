# Hacker News Agent

自动爬取 Hacker News 专项新闻并推送到微信的工具。

## 功能特性

- 每天定时爬取 Hacker News Top Stories
- 按热度（点赞数）和关键词过滤
- 自动推送到微信（通过 Server酱）
- SQLite 存储已推送记录，避免重复
- 失败重试机制
- 健康检查和日志记录

## 技术栈

- Python 3.11+
- httpx - HTTP 客户端
- APScheduler - 定时任务
- SQLite - 数据存储
- Server酱 - 微信推送

## 快速开始

### 1. 安装依赖

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置

复制环境变量模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 Server酱 SendKey：

```
SERVERCHAN_KEY=your_send_key_here
```

### 3. 运行

```bash
python -m src.main
```

## 配置说明

配置文件位于 `config/config.yaml`：

```yaml
hackernews:
  top_stories_limit: 30      # 拉取数量
  request_delay: 0.1         # 请求间隔（秒）

filter:
  min_score: 50              # 最低点赞数
  keywords:                  # 包含关键词
    - ai
    - llm
    - agent
    - python
  exclude:                   # 排除关键词
    - hiring

serverchan:
  send_key: "${SERVERCHAN_KEY}"

scheduler:
  cron: "0 8 * * *"         # 每天 08:00 执行
  timezone: "Asia/Shanghai"
```

## 项目结构

```
hacker-news-agent/
├── src/
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
│   ├── config.yaml          # 配置文件
│   └── hackernews.service   # systemd 服务
├── tests/                   # 单元测试
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 模块说明

| 模块 | 职责 |
|------|------|
| `scraper` | 从 HN API 拉取帖子 |
| `filter` | 按热度+关键词过滤 |
| `formatter` | 格式化为 Markdown |
| `notifier` | 调用 Server酱推送 |
| `database` | SQLite 状态存储 |
| `health` | 健康检查 |
| `scheduler` | 定时任务调度 |

## 部署

### Docker 部署

```bash
docker-compose up -d
```

### systemd 部署

```bash
sudo cp config/hackernews.service /etc/systemd/system/
sudo systemctl enable hackernews
sudo systemctl start hackernews
```

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码规范

- 使用 type hints
- 遵循 PEP 8
- 每个模块职责单一

## License

MIT
