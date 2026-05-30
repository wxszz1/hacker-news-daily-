# Hacker News Agent

Automatically scrape Hacker News for AI/Agent-related articles and push daily digests to WeChat.

## Features

- Daily scheduled scraping of HN Top Stories
- Filter by score (popularity) and keywords
- Auto-push to WeChat via Server酱
- SQLite storage for deduplication
- Retry mechanism for failed pushes
- Health check and logging

## Tech Stack

- Python 3.11+
- httpx - HTTP client
- APScheduler - Cron jobs
- SQLite - State storage
- Server酱 - WeChat push

## Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

Copy environment variables template:

```bash
cp .env.example .env
```

Edit `.env` with your Server酱 SendKey:

```
SERVERCHAN_KEY=your_send_key_here
```

### 3. Run

```bash
python -m src.main
```

## Configuration

Edit `config/config.yaml`:

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
    - python

scheduler:
  cron: "0 8 * * *"
  timezone: "Asia/Shanghai"
```

## Project Structure

```
hacker-news-agent/
├── src/
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration
│   ├── scraper.py           # HN API client
│   ├── filter.py            # Article filter
│   ├── formatter.py         # Message formatter
│   ├── notifier.py          # Server酱 push
│   ├── database.py          # SQLite storage
│   ├── health.py            # Health check
│   └── scheduler.py         # Cron scheduler
├── config/
│   └── config.yaml
├── tests/
├── Dockerfile
└── docker-compose.yml
```

## Deployment

### Docker

```bash
docker-compose up -d
```

### systemd

```bash
sudo cp config/hackernews.service /etc/systemd/system/
sudo systemctl enable hackernews
sudo systemctl start hackernews
```

## Development

### Run Tests

```bash
pytest tests/
```

## License

MIT
