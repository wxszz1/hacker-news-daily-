# Hacker News Agent

Scheduled Hacker News digest. It fetches top stories, filters them, optionally enriches them with a Zhipu GLM agent, and pushes a Markdown digest to WeChat through Server酱.

## Features

- Fetches Hacker News top stories on a cron schedule (APScheduler)
- Filters by minimum score, include keywords, exclude keywords, and stories already pushed
- Stores push records and a short-lived cache in SQLite
- Pushes to WeChat via Server酱, and retries failed pushes
- Health check and rotating file logs
- Optional GLM pipeline when `ZHIPU_API_KEY` is set and `agent.enabled` is true: importance score, summary, and research notes for high-score stories. If the key is missing, this step is skipped and the digest is still built
- `run_agent_task()` in `src/main.py` runs a tool-using agent (search, fetch, LLM, notify, translate). `python -m src.main` does not start that interactive task

`Translator` and `Classifier` are included. The scheduled formatter prints a Chinese title or category only when those fields are already set on a story. The daily job does not fill them itself.

## Requirements

- Python 3.11+
- Packages in `requirements.txt`: httpx, PyYAML, APScheduler, python-dotenv, Pydantic 2, readability-lxml
- SQLite from the Python standard library
- A Server酱 SendKey for WeChat push
- An optional Zhipu GLM API key. The default model in `config/config.yaml` is `glm-4-flash`

## Install

From the repository root:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate the virtual environment with `venv\Scripts\activate`.

## Configure

Create a local env file from the placeholder template:

```bash
cp .env.example .env
```

`.env` is gitignored. The program reads these variables:

| Variable | Required | Effect when empty |
| --- | --- | --- |
| `SERVERCHAN_KEY` | Required to push | `ServerChanNotifier` rejects the key and does not push |
| `ZHIPU_API_KEY` | Optional | Scoring, summaries, research, and `run_agent_task()` stay off |
| `BAIDU_FANYI_APPID` | Optional | Baidu translation stays off unless both Baidu variables are set |
| `BAIDU_FANYI_SECRET` | Optional | Same as `BAIDU_FANYI_APPID` |

Non-secret settings are in `config/config.yaml`:

- `hackernews.top_stories_limit`, `hackernews.request_delay`
- `filter.min_score`, `filter.keywords`, `filter.exclude`
- `database.path` (default `data/hackernews.db`)
- `logging.level`, `logging.file`, `logging.max_bytes`, `logging.backup_count`
- `scheduler.cron` (default `0 8 * * *`), `scheduler.timezone` (default `Asia/Shanghai`)
- `agent.enabled`, plus nested `llm`, `scorer`, `summarizer`, and `researcher` settings

Do not put API keys in `config/config.yaml`. The SendKey is read from `SERVERCHAN_KEY`, not from the YAML file.

## Run

From the repository root, with the virtual environment active:

```bash
python -m src.main
```

This loads `.env` and `config/config.yaml`, writes a health-check log, retries failed pushes on a background thread, and starts the scheduler. The process keeps running until it is stopped.

To run one agent task instead of the scheduler, set `ZHIPU_API_KEY` and execute:

```bash
python -c "from src.main import run_agent_task; print(run_agent_task('搜索关于 AI Agent 的最新文章'))"
```

Without `ZHIPU_API_KEY`, that call returns `Agent 未启用，请配置 ZHIPU_API_KEY` and does not contact the LLM.

## Test

Install the test runner in the same virtual environment. pytest and pytest-asyncio are not in `requirements.txt`:

```bash
pip install pytest pytest-asyncio
pytest tests/
```

`tests/test_agent.py` contacts the live LLM only when `ZHIPU_API_KEY` is set. With an empty key it returns immediately. The other tests mock HTTP calls and use temporary files. They do not need a network connection or real credentials.

## Deployment

### Docker Compose

Create `.env` before starting. Compose supplies that file to the container and mounts `config/`, `data/`, and `logs/`.

```bash
docker-compose up -d --build
```

### systemd

`deploy.sh` installs Python 3.11, clones the repository to `/opt/hacker-news-agent`, creates a virtual environment, copies `.env.example` to `.env`, and installs `config/hackernews.service`.

The unit file is written for user `ubuntu` and this start command:

```
/opt/hacker-news-agent/venv/bin/python -m src.main
```

Change the user and paths if the host differs. Replace the `<your-repo>` clone URL in `deploy.sh` before running it. Do not commit `.env` or a deploy key.

## Project layout

```
src/                  scheduled job, scraper, filter, notifier, agent pipeline
src/agent/            planner, tools, memory, reflector
src/tools/            search, fetch, llm, notify, translate
config/config.yaml    non-secret settings
config/hackernews.service
deploy.sh             host install script
tests/                unit tests
docs/superpowers/     design and implementation notes
```

## License

MIT
