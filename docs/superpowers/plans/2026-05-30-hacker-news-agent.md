# Hacker News Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python tool that automatically scrapes Hacker News for AI/Agent-related articles and pushes daily digests to WeChat via Server酱.

**Architecture:** Modular design with 7 independent components (scraper, filter, formatter, notifier, database, health, scheduler) coordinated by a main entry point. Each module has a single responsibility and can be tested in isolation.

**Tech Stack:** Python 3.11+, httpx, PyYAML, Pydantic, SQLite, APScheduler, Server酱

---

## Review Standards (审查标准)

### General Review Criteria (通用审查标准)

Every task must pass these checks:

| Category | Check | Pass Condition |
|----------|-------|----------------|
| **File Existence** | All required files exist | 100% files present |
| **File Content** | Content matches spec exactly | No deviations from plan |
| **Tests Pass** | `pytest tests/ -v` | All tests pass, 0 failures |
| **No Regressions** | Existing tests still pass | No test regressions |
| **Code Quality** | Follows project conventions | Consistent style |

### Task-Specific Review Criteria (任务专项审查标准)

Each task has specific review criteria listed below.

### Review Process (审查流程)

1. **Implementer Self-Review**: After implementation, run tests and verify
2. **Spec Compliance Review**: Verify code matches plan specification
3. **Code Quality Review**: Check code style, error handling, documentation
4. **Regression Check**: Run full test suite to ensure no breakage

### Review Verdicts (审查结论)

| Verdict | Meaning | Action |
|---------|---------|--------|
| **PASS** | All criteria met | Proceed to next task |
| **PASS_WITH_NOTES** | Minor issues noted | Proceed, address later |
| **FAIL** | Critical issues found | Fix before proceeding |

---

## File Structure

```
hacker-news-agent/
├── src/
│   ├── __init__.py              # Package marker
│   ├── config.py                # Configuration loading & validation
│   ├── logging_config.py        # Structured logging setup
│   ├── scraper.py               # Hacker News API client
│   ├── filter.py                # Article filtering (score + keywords)
│   ├── formatter.py             # Markdown message formatting
│   ├── notifier.py              # Server酱 push notifications
│   ├── database.py              # SQLite state management
│   ├── health.py                # Health check reporting
│   ├── scheduler.py             # APScheduler cron wrapper
│   └── main.py                  # Entry point & orchestration
├── config/
│   ├── config.yaml              # Main configuration
│   └── hackernews.service       # systemd service file
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_filter.py
│   ├── test_formatter.py
│   ├── test_health.py
│   ├── test_notifier.py
│   └── test_scraper.py
├── docs/
│   └── superpowers/
│       ├── specs/               # Design specifications
│       └── plans/               # This file
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── deploy.sh
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`

**Review Criteria:**
- [ ] requirements.txt contains all 5 dependencies (httpx, pyyaml, apscheduler, python-dotenv, pydantic)
- [ ] .gitignore contains venv/, __pycache__/, .env, data/, logs/
- [ ] .env.example contains SERVERCHAN_KEY placeholder
- [ ] src/__init__.py exists
- [ ] tests/__init__.py exists
- [ ] `pytest tests/ -v` passes (37 tests)
- Create: `.env.example`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create project root files**

```bash
cd hacker-news-agent
git init
```

- [ ] **Step 2: Create requirements.txt**

```
httpx>=0.24.0
pyyaml>=6.0
apscheduler>=3.10.0
python-dotenv>=1.0.0
pydantic>=2.0.0
```

- [ ] **Step 3: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/
dist/
build/

# Data and logs
data/
logs/

# Environment
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# System
.DS_Store
Thumbs.db
```

- [ ] **Step 4: Create .env.example**

```bash
# Server酱 SendKey
SERVERCHAN_KEY=your_send_key_here

# Optional: Debug mode
DEBUG=false
```

- [ ] **Step 5: Create package markers**

```python
# src/__init__.py
# Hacker News Agent

# tests/__init__.py
# Tests
```

- [ ] **Step 6: Install dependencies and verify**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

- [ ] **Step 7: Commit**

```bash
git add .
git commit -m "feat: initial project scaffolding"
```

---

## Task 2: Configuration Module

**Files:**
- Create: `src/config.py`
- Create: `config/config.yaml`
- Create: `tests/test_config.py`

**Review Criteria:**
- [ ] config.py contains all config classes (HackerNewsConfig, FilterConfig, ServerChanConfig, DatabaseConfig, LoggingConfig, SchedulerConfig, AppConfig)
- [ ] config.py has get_project_root() function
- [ ] config.py has load_config() function with path handling
- [ ] config.yaml contains all required sections (hackernews, filter, serverchan, database, logging, scheduler)
- [ ] config.yaml exclude list uses quoted string for "ask hn: who is hiring"
- [ ] test_config.py has 5 tests (load_config_success, load_config_missing_file, filter_config_validation, filter_config_empty_keywords, filter_config_keywords_lowercase)
- [ ] `pytest tests/test_config.py -v` passes (5 tests)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import pytest
from src.config import load_config, AppConfig, FilterConfig

def test_load_config_success():
    """Test successful config loading"""
    config = load_config("config/config.yaml")
    assert isinstance(config, AppConfig)
    assert config.hackernews.top_stories_limit == 30
    assert config.filter.min_score == 50
    assert "ai" in config.filter.keywords

def test_load_config_missing_file():
    """Test config file not found"""
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent.yaml")

def test_filter_config_validation():
    """Test filter config validation"""
    config = FilterConfig(min_score=100, keywords=["test"])
    assert config.min_score == 100
    assert config.keywords == ["test"]

def test_filter_config_empty_keywords():
    """Test empty keywords validation"""
    with pytest.raises(ValueError):
        FilterConfig(keywords=[])

def test_filter_config_keywords_lowercase():
    """Test keywords auto-lowercase"""
    config = FilterConfig(keywords=["AI", "LLM", "Python"])
    assert config.keywords == ["ai", "llm", "python"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_config.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.config'"

- [ ] **Step 3: Write config.yaml**

```yaml
# config/config.yaml
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
    - "ask hn: who is hiring"

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

- [ ] **Step 4: Write config.py implementation**

```python
# src/config.py
import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic import validator

class HackerNewsConfig(BaseModel):
    top_stories_limit: int = Field(default=30, ge=1, le=100)
    request_delay: float = Field(default=0.1, ge=0.05, le=1.0)

class FilterConfig(BaseModel):
    min_score: int = Field(default=50, ge=0)
    keywords: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)

    @validator("keywords")
    def validate_keywords(cls, v):
        if not v:
            raise ValueError("keywords cannot be empty")
        return [kw.lower() for kw in v]

class ServerChanConfig(BaseModel):
    send_key: str = Field(
        default_factory=lambda: os.getenv("SERVERCHAN_KEY", "")
    )

class DatabaseConfig(BaseModel):
    path: str = Field(default="data/hackernews.db")

class LoggingConfig(BaseModel):
    level: str = Field(default="INFO")
    file: str = Field(default="logs/app.log")
    max_bytes: int = Field(default=10485760)
    backup_count: int = Field(default=5)

class SchedulerConfig(BaseModel):
    cron: str = Field(default="0 8 * * *")
    timezone: str = Field(default="Asia/Shanghai")

class AppConfig(BaseModel):
    hackernews: HackerNewsConfig = Field(default_factory=HackerNewsConfig)
    filter: FilterConfig
    serverchan: ServerChanConfig = Field(default_factory=ServerChanConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)

def get_project_root() -> Path:
    """Get project root directory"""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "config").exists() and (current / "src").exists():
            return current
        current = current.parent
    return Path(__file__).parent.parent

def load_config(config_path: str = None) -> AppConfig:
    """Load and validate configuration file"""
    project_root = get_project_root()

    if config_path is None:
        config_path = project_root / "config" / "config.yaml"

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Handle database and log paths with absolute paths
    if "database" in data and "path" in data["database"]:
        db_path = Path(data["database"]["path"])
        if not db_path.is_absolute():
            data["database"]["path"] = str(project_root / db_path)

    if "logging" in data and "file" in data["logging"]:
        log_path = Path(data["logging"]["file"])
        if not log_path.is_absolute():
            data["logging"]["file"] = str(project_root / log_path)

    try:
        return AppConfig(**data)
    except Exception as e:
        raise ValueError(f"Config validation failed: {e}")
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_config.py -v
```

Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add src/config.py config/config.yaml tests/test_config.py
git commit -m "feat: add configuration module with Pydantic validation"
```

---

## Task 3: Logging Module

**Files:**
- Create: `src/logging_config.py`

**Review Criteria:**
- [ ] logging_config.py has setup_logging() function
- [ ] setup_logging() accepts config dict with level, file, max_bytes, backup_count
- [ ] Uses RotatingFileHandler for log rotation
- [ ] Creates log directory if not exists
- [ ] Configures both file and console handlers

- [ ] **Step 1: Write logging_config.py**

```python
# src/logging_config.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(config: dict):
    """Configure structured logging with rotation"""
    log_path = Path(config["file"])
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        config["file"],
        maxBytes=config["max_bytes"],
        backupCount=config["backup_count"],
        encoding="utf-8"
    )

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logging.basicConfig(
        level=config["level"],
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            handler,
            logging.StreamHandler()
        ]
    )
```

- [ ] **Step 2: Commit**

```bash
git add src/logging_config.py
git commit -m "feat: add structured logging with file rotation"
```

---

## Task 4: Database Module

**Files:**
- Create: `src/database.py`
- Create: `tests/test_database.py`

**Review Criteria:**
- [ ] database.py has Database class with context manager
- [ ] database.py creates pushed_articles and failed_pushes tables
- [ ] database.py has get_pushed_ids() and record_pushed() methods
- [ ] test_database.py has 7 tests
- [ ] All tests use temporary database (no side effects)
- [ ] `pytest tests/test_database.py -v` passes (7 tests)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_database.py
import pytest
import tempfile
from pathlib import Path
from src.database import Database

@pytest.fixture
def db():
    """Create temporary database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        database = Database(str(db_path))
        yield database

def test_database_init(db):
    """Test database initialization"""
    assert db.db_path.exists()

def test_get_pushed_ids_empty(db):
    """Test get pushed IDs - empty database"""
    ids = db.get_pushed_ids()
    assert ids == set()

def test_record_pushed(db):
    """Test record pushed article"""
    db.record_pushed(123, "Test Article")
    ids = db.get_pushed_ids()
    assert 123 in ids

def test_record_pushed_duplicate(db):
    """Test record duplicate pushed article"""
    db.record_pushed(123, "Test Article")
    db.record_pushed(123, "Test Article Again")
    ids = db.get_pushed_ids()
    assert len(ids) == 1

def test_get_pushed_ids_multiple(db):
    """Test get multiple pushed IDs"""
    db.record_pushed(123, "Article 1")
    db.record_pushed(456, "Article 2")
    db.record_pushed(789, "Article 3")
    ids = db.get_pushed_ids()
    assert ids == {123, 456, 789}

def test_database_context_manager(db):
    """Test database context manager"""
    with db.get_connection() as conn:
        conn.execute("SELECT 1")

def test_database_rollback(db):
    """Test database rollback on error"""
    try:
        with db.get_connection() as conn:
            conn.execute("INSERT INTO pushed_articles (article_id, title) VALUES (1, 'Test')")
            raise Exception("Simulated error")
    except Exception:
        pass

    ids = db.get_pushed_ids()
    assert 1 not in ids
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_database.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write database.py implementation**

```python
# src/database.py
import sqlite3
from contextlib import contextmanager
from pathlib import Path

class Database:
    def __init__(self, db_path: str = "data/hackernews.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def get_connection(self):
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
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS pushed_articles (
                    id INTEGER PRIMARY KEY,
                    article_id INTEGER UNIQUE,
                    title TEXT,
                    pushed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS failed_pushes (
                    id INTEGER PRIMARY KEY,
                    message TEXT,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    retry_count INTEGER DEFAULT 0
                );
            """)

    def get_pushed_ids(self) -> set[int]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT article_id FROM pushed_articles").fetchall()
            return {row[0] for row in rows}

    def record_pushed(self, article_id: int, title: str):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO pushed_articles (article_id, title) VALUES (?, ?)",
                (article_id, title)
            )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_database.py -v
```

Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/database.py tests/test_database.py
git commit -m "feat: add SQLite database module with context manager"
```

---

## Task 5: Scraper Module

**Files:**
- Create: `src/scraper.py`
- Create: `tests/test_scraper.py`

**Review Criteria:**
- [ ] scraper.py has HackerNewsScraper class with BASE_URL, REQUEST_DELAY, TIMEOUT
- [ ] scraper.py has sync and async methods (no duplicate method names)
- [ ] scraper.py handles timeout and network errors gracefully
- [ ] test_scraper.py has 4 tests
- [ ] Tests use mocking (no real API calls)
- [ ] `pytest tests/test_scraper.py -v` passes (4 tests)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scraper.py
import pytest
from unittest.mock import Mock, patch
from src.scraper import HackerNewsScraper

def test_scraper_init():
    """Test scraper initialization"""
    scraper = HackerNewsScraper()
    assert scraper.BASE_URL == "https://hacker-news.firebaseio.com/v0"
    assert scraper.REQUEST_DELAY == 0.1
    assert scraper.TIMEOUT == 10.0

@patch('src.scraper.httpx.Client')
def test_fetch_ids_sync_success(mock_client):
    """Test sync fetch IDs success"""
    mock_response = Mock()
    mock_response.json.return_value = [123, 456, 789]
    mock_response.raise_for_status = Mock()
    mock_client.return_value.__enter__.return_value.get.return_value = mock_response

    scraper = HackerNewsScraper()
    ids = scraper._fetch_ids_sync(mock_client.return_value.__enter__.return_value, "topstories")

    assert ids == [123, 456, 789]

@patch('src.scraper.httpx.Client')
def test_fetch_ids_sync_failure(mock_client):
    """Test sync fetch IDs failure"""
    mock_client.return_value.__enter__.return_value.get.side_effect = Exception("Network error")

    scraper = HackerNewsScraper()
    ids = scraper._fetch_ids_sync(mock_client.return_value.__enter__.return_value, "topstories")

    assert ids == []

@patch('src.scraper.httpx.Client')
@patch('src.scraper.time.sleep')
def test_get_story_detail_sync_success(mock_sleep, mock_client):
    """Test sync get story detail success"""
    mock_response = Mock()
    mock_response.json.return_value = {"id": 123, "title": "Test", "score": 100}
    mock_response.raise_for_status = Mock()
    mock_client.return_value.__enter__.return_value.get.return_value = mock_response

    scraper = HackerNewsScraper()
    story = scraper._get_story_detail_sync(mock_client.return_value.__enter__.return_value, 123)

    assert story["id"] == 123
    assert story["title"] == "Test"

@patch('src.scraper.httpx.Client')
@patch('src.scraper.time.sleep')
def test_get_story_detail_sync_not_found(mock_sleep, mock_client):
    """Test sync get story detail - not found"""
    mock_response = Mock()
    mock_response.json.return_value = None
    mock_response.raise_for_status = Mock()
    mock_client.return_value.__enter__.return_value.get.return_value = mock_response

    scraper = HackerNewsScraper()
    story = scraper._get_story_detail_sync(mock_client.return_value.__enter__.return_value, 999)

    assert story is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_scraper.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write scraper.py implementation**

```python
# src/scraper.py
import httpx
import time
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class HackerNewsScraper:
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    REQUEST_DELAY = 0.1
    TIMEOUT = 10.0

    def __init__(self, use_async: bool = False):
        self.use_async = use_async

    def fetch_top_stories_sync(self, limit: int = 30) -> list[dict]:
        """Sync fetch top stories"""
        try:
            with httpx.Client(timeout=self.TIMEOUT) as client:
                story_ids = self._fetch_ids_sync(client, "topstories")
                if not story_ids:
                    logger.warning("No story IDs fetched")
                    return []

                results = []
                for sid in story_ids[:limit]:
                    story = self._get_story_detail_sync(client, sid)
                    if story:
                        results.append(story)
                return results
        except httpx.TimeoutException:
            logger.error("Timeout fetching stories from HN API")
            return []
        except httpx.RequestError as e:
            logger.error(f"Network error fetching stories: {e}")
            return []

    async def fetch_top_stories(self, limit: int = 30) -> list[dict]:
        """Async fetch top stories"""
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                story_ids = await self._fetch_ids_async(client, "topstories")
                if not story_ids:
                    logger.warning("No story IDs fetched")
                    return []

                tasks = [self._get_story_detail_async(client, sid) for sid in story_ids[:limit]]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return [r for r in results if r is not None]
        except httpx.TimeoutException:
            logger.error("Timeout fetching stories from HN API")
            return []
        except httpx.RequestError as e:
            logger.error(f"Network error fetching stories: {e}")
            return []

    def _fetch_ids_sync(self, client: httpx.Client, endpoint: str) -> list[int]:
        """Sync fetch story ID list"""
        try:
            resp = client.get(f"{self.BASE_URL}/{endpoint}.json")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch IDs: {e}")
            return []

    async def _fetch_ids_async(self, client: httpx.AsyncClient, endpoint: str) -> list[int]:
        """Async fetch story ID list"""
        try:
            resp = await client.get(f"{self.BASE_URL}/{endpoint}.json")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch IDs: {e}")
            return []

    def _get_story_detail_sync(self, client: httpx.Client, story_id: int) -> Optional[dict]:
        """Sync get single story detail"""
        time.sleep(self.REQUEST_DELAY)
        try:
            resp = client.get(f"{self.BASE_URL}/item/{story_id}.json")
            resp.raise_for_status()
            data = resp.json()
            if data is None:
                logger.warning(f"Story {story_id} not found")
                return None
            return data
        except Exception as e:
            logger.error(f"Failed to fetch story {story_id}: {e}")
            return None

    async def _get_story_detail_async(self, client: httpx.AsyncClient, story_id: int) -> Optional[dict]:
        """Async get single story detail"""
        await asyncio.sleep(self.REQUEST_DELAY)
        try:
            resp = await client.get(f"{self.BASE_URL}/item/{story_id}.json")
            resp.raise_for_status()
            data = resp.json()
            if data is None:
                logger.warning(f"Story {story_id} not found")
                return None
            return data
        except Exception as e:
            logger.error(f"Failed to fetch story {story_id}: {e}")
            return None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_scraper.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/scraper.py tests/test_scraper.py
git commit -m "feat: add HN API scraper with timeout and error handling"
```

---

## Task 6: Filter Module

**Files:**
- Create: `src/filter.py`
- Create: `tests/test_filter.py`

**Review Criteria:**
- [ ] filter.py has NewsFilter class with filter(), _filter_by_score(), _filter_by_keywords(), _exclude_by_keywords(), _deduplicate()
- [ ] filter.py does NOT fall back to score-only filtering (returns empty if no keyword match)
- [ ] test_filter.py has 8 tests
- [ ] Tests cover: score filtering, keyword filtering, exclusion, deduplication, empty input, no keyword match
- [ ] `pytest tests/test_filter.py -v` passes (8 tests)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_filter.py
import pytest
from src.filter import NewsFilter
from src.config import FilterConfig

@pytest.fixture
def filter_config():
    return FilterConfig(
        min_score=50,
        keywords=["ai", "llm", "python"],
        exclude=["hiring"]
    )

@pytest.fixture
def news_filter(filter_config):
    return NewsFilter(filter_config)

def test_filter_by_score(news_filter):
    """Test filter by score"""
    stories = [
        {"id": 1, "title": "AI News", "score": 100},
        {"id": 2, "title": "Low Score", "score": 30},
        {"id": 3, "title": "High Score", "score": 60},
    ]
    result = news_filter._filter_by_score(stories)
    assert len(result) == 2
    assert all(s["score"] >= 50 for s in result)

def test_filter_by_keywords(news_filter):
    """Test filter by keywords"""
    stories = [
        {"id": 1, "title": "AI is great", "score": 100},
        {"id": 2, "title": "Python tutorial", "score": 100},
        {"id": 3, "title": "JavaScript basics", "score": 100},
    ]
    result = news_filter._filter_by_keywords(stories)
    assert len(result) == 2
    assert any("AI" in s["title"] for s in result)
    assert any("Python" in s["title"] for s in result)

def test_exclude_by_keywords(news_filter):
    """Test exclude by keywords"""
    stories = [
        {"id": 1, "title": "AI News", "score": 100},
        {"id": 2, "title": "Who is hiring?", "score": 100},
        {"id": 3, "title": "Python tips", "score": 100},
    ]
    result = news_filter._exclude_by_keywords(stories)
    assert len(result) == 2
    assert not any("hiring" in s["title"].lower() for s in result)

def test_deduplicate(news_filter):
    """Test deduplication"""
    stories = [
        {"id": 1, "title": "AI News", "score": 100},
        {"id": 2, "title": "Python tips", "score": 100},
        {"id": 3, "title": "LLM update", "score": 100},
    ]
    pushed_ids = {1, 3}
    result = news_filter._deduplicate(stories, pushed_ids)
    assert len(result) == 1
    assert result[0]["id"] == 2

def test_filter_full_flow(news_filter):
    """Test full filter flow"""
    stories = [
        {"id": 1, "title": "AI is great", "score": 100},
        {"id": 2, "title": "Low score AI", "score": 30},
        {"id": 3, "title": "JavaScript basics", "score": 100},
        {"id": 4, "title": "Who is hiring?", "score": 100},
        {"id": 5, "title": "Python tips", "score": 60},
    ]
    pushed_ids = {1}
    result = news_filter.filter(stories, pushed_ids)
    assert len(result) == 1
    assert result[0]["id"] == 5

def test_filter_empty_input(news_filter):
    """Test empty input"""
    result = news_filter.filter([], set())
    assert result == []

def test_filter_no_keyword_match():
    """Test no keyword match returns empty"""
    config = FilterConfig(
        min_score=50,
        keywords=["very_specific_keyword"],
        exclude=[]
    )
    news_filter = NewsFilter(config)

    stories = [
        {"id": 1, "title": "General AI News", "score": 100},
        {"id": 2, "title": "Python tutorial", "score": 80},
        {"id": 3, "title": "JavaScript basics", "score": 70},
    ]
    result = news_filter.filter(stories, set())
    assert len(result) == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_filter.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write filter.py implementation**

```python
# src/filter.py
import logging

logger = logging.getLogger(__name__)

class NewsFilter:
    def __init__(self, config):
        self.min_score = config.min_score
        self.keywords = [kw.lower() for kw in config.keywords]
        self.exclude_keywords = [kw.lower() for kw in config.exclude]

    def filter(self, stories: list[dict], pushed_ids: set[int]) -> list[dict]:
        """Filter by score, keywords, then deduplicate"""
        if not stories:
            return []

        # Step 1: Filter by score
        high_score_stories = self._filter_by_score(stories)
        if not high_score_stories:
            logger.info("No stories meet minimum score threshold")
            return []

        # Step 2: Filter by keywords
        keyword_filtered = self._filter_by_keywords(high_score_stories)

        # Step 3: If no keyword matches, skip push (avoid unrelated content)
        if not keyword_filtered:
            logger.info("No stories match keywords, skipping push")
            return []

        # Step 4: Exclude excluded keywords
        result = self._exclude_by_keywords(keyword_filtered)

        # Step 5: Deduplicate
        result = self._deduplicate(result, pushed_ids)

        logger.info(f"Filtered {len(stories)} -> {len(result)} stories")
        return result

    def _filter_by_score(self, stories: list[dict]) -> list[dict]:
        return [s for s in stories if s.get("score", 0) >= self.min_score]

    def _filter_by_keywords(self, stories: list[dict]) -> list[dict]:
        if not self.keywords:
            return stories

        return [s for s in stories
                if any(kw in s.get("title", "").lower() for kw in self.keywords)]

    def _exclude_by_keywords(self, stories: list[dict]) -> list[dict]:
        if not self.exclude_keywords:
            return stories

        return [s for s in stories
                if not any(kw in s.get("title", "").lower() for kw in self.exclude_keywords)]

    def _deduplicate(self, stories: list[dict], pushed_ids: set[int]) -> list[dict]:
        if not pushed_ids:
            return stories

        return [s for s in stories if s["id"] not in pushed_ids]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_filter.py -v
```

Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add src/filter.py tests/test_filter.py
git commit -m "feat: add news filter with score and keyword matching"
```

---

## Task 7: Formatter Module

**Files:**
- Create: `src/formatter.py`
- Create: `tests/test_formatter.py`

**Review Criteria:**
- [ ] formatter.py has MessageFormatter class with format() and _format_age()
- [ ] format() returns Markdown with title, URL, score, comments, age
- [ ] format() handles missing URLs (falls back to HN item URL)
- [ ] format() returns None for empty input
- [ ] test_formatter.py has 5 tests
- [ ] `pytest tests/test_formatter.py -v` passes (5 tests)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_formatter.py
import pytest
from datetime import datetime
from src.formatter import MessageFormatter

@pytest.fixture
def formatter():
    return MessageFormatter()

def test_format_stories(formatter):
    """Test format stories"""
    stories = [
        {
            "id": 1,
            "title": "AI is great",
            "url": "https://example.com",
            "score": 100,
            "descendants": 50,
            "time": int(datetime.now().timestamp()) - 3600
        },
        {
            "id": 2,
            "title": "Python tips",
            "url": "https://python.org",
            "score": 80,
            "descendants": 30,
            "time": int(datetime.now().timestamp()) - 7200
        }
    ]
    result = formatter.format(stories)
    assert result is not None
    assert "Hacker News 早报" in result
    assert "AI is great" in result
    assert "Python tips" in result
    assert "👍 100" in result
    assert "💬 50" in result

def test_format_empty_stories(formatter):
    """Test format empty stories"""
    result = formatter.format([])
    assert result is None

def test_format_age_hours(formatter):
    """Test format age - hours"""
    timestamp = int(datetime.now().timestamp()) - 3600
    result = formatter._format_age(timestamp)
    assert "h ago" in result

def test_format_age_days(formatter):
    """Test format age - days"""
    timestamp = int(datetime.now().timestamp()) - 86400 * 2
    result = formatter._format_age(timestamp)
    assert "d ago" in result

def test_format_no_url(formatter):
    """Test format story without URL"""
    stories = [
        {
            "id": 1,
            "title": "Ask HN: Question",
            "score": 100,
            "descendants": 50,
            "time": int(datetime.now().timestamp()) - 3600
        }
    ]
    result = formatter.format(stories)
    assert "Ask HN: Question" in result
    assert "news.ycombinator.com" in result
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_formatter.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write formatter.py implementation**

```python
# src/formatter.py
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MessageFormatter:
    def format(self, stories: list[dict]) -> str:
        """Format stories as Markdown message"""
        if not stories:
            return None

        date_str = datetime.now().strftime("%Y-%m-%d")
        lines = [f"📰 Hacker News 早报 ({date_str})", ""]

        for i, story in enumerate(stories, 1):
            title = story.get("title", "Untitled")
            url = story.get("url", f"https://news.ycombinator.com/item?id={story['id']}")
            score = story.get("score", 0)
            comments = story.get("descendants", 0)
            age = self._format_age(story.get("time", 0))

            lines.append(f"{i}. [{title}]({url})")
            lines.append(f"   👍 {score} | 💬 {comments} | 🕐 {age}")
            lines.append("")

        return "\n".join(lines)

    def _format_age(self, timestamp: int) -> str:
        delta = datetime.now().timestamp() - timestamp
        hours = int(delta // 3600)
        return f"{hours}h ago" if hours < 24 else f"{hours // 24}d ago"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_formatter.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/formatter.py tests/test_formatter.py
git commit -m "feat: add Markdown message formatter"
```

---

## Task 8: Notifier Module

**Files:**
- Create: `src/notifier.py`
- Create: `tests/test_notifier.py`

**Review Criteria:**
- [ ] notifier.py has ServerChanNotifier class with send(), _record_failure(), retry_failed()
- [ ] send() implements retry with exponential backoff (MAX_RETRIES = 3)
- [ ] send() records failure to SQLite after max retries
- [ ] retry_failed() reads from failed_pushes and retries
- [ ] test_notifier.py has 5 tests
- [ ] Tests use mocking (no real API calls)
- [ ] `pytest tests/test_notifier.py -v` passes (5 tests)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_notifier.py
import pytest
from unittest.mock import Mock, patch
from src.notifier import ServerChanNotifier
from src.database import Database
import tempfile
from pathlib import Path

@pytest.fixture
def db():
    """Create temporary database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        database = Database(str(db_path))
        yield database

@pytest.fixture
def notifier(db):
    return ServerChanNotifier("test_send_key", db)

@patch('src.notifier.httpx.post')
def test_send_success(mock_post, notifier):
    """Test send success"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result = notifier.send("Test Title", "Test Content")
    assert result is True

@patch('src.notifier.httpx.post')
def test_send_failure(mock_post, notifier):
    """Test send failure"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response

    result = notifier.send("Test Title", "Test Content")
    assert result is False

@patch('src.notifier.httpx.post')
def test_send_exception(mock_post, notifier):
    """Test send exception"""
    mock_post.side_effect = Exception("Network error")

    result = notifier.send("Test Title", "Test Content")
    assert result is False

@patch('src.notifier.httpx.post')
def test_send_retry(mock_post, notifier):
    """Test send retry"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response

    notifier.send("Test Title", "Test Content")
    assert mock_post.call_count == 3

def test_record_failure(notifier):
    """Test record failure"""
    notifier._record_failure("Test Title", "Test Content")

    with notifier.db.get_connection() as conn:
        failures = conn.execute("SELECT * FROM failed_pushes").fetchall()
        assert len(failures) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_notifier.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write notifier.py implementation**

```python
# src/notifier.py
import httpx
import time
import logging

logger = logging.getLogger(__name__)

class ServerChanNotifier:
    API_URL = "https://sctapi.ftqq.com/{key}.send"
    MAX_RETRIES = 3

    def __init__(self, send_key: str, db):
        self.send_key = send_key
        self.db = db

    def send(self, title: str, content: str) -> bool:
        """Send message, record failure if max retries exceeded"""
        for attempt in range(self.MAX_RETRIES):
            try:
                resp = httpx.post(
                    self.API_URL.format(key=self.send_key),
                    data={"title": title, "desp": content}
                )
                if resp.status_code == 200:
                    return True
            except Exception as e:
                logger.warning(f"Push attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)

        self._record_failure(title, content)
        return False

    def _record_failure(self, title: str, content: str):
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO failed_pushes (message, error) VALUES (?, ?)",
                (f"{title}\n{content}", "max retries exceeded")
            )

    def retry_failed(self):
        """Retry failed pushes"""
        with self.db.get_connection() as conn:
            failures = conn.execute(
                "SELECT id, message FROM failed_pushes WHERE retry_count < 3"
            ).fetchall()

        for failure_id, message in failures:
            title, content = message.split("\n", 1)
            if self.send(title, content):
                with self.db.get_connection() as conn:
                    conn.execute("DELETE FROM failed_pushes WHERE id = ?", (failure_id,))
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_notifier.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/notifier.py tests/test_notifier.py
git commit -m "feat: add Server酱 notifier with retry mechanism"
```

---

## Task 9: Health Check Module

**Files:**
- Create: `src/health.py`
- Create: `tests/test_health.py`

**Review Criteria:**
- [ ] health.py has HealthChecker class with check_daily_job() and log_health_status()
- [ ] check_daily_job() returns dict with last_push, failed_count, pushed_today, healthy
- [ ] healthy is True only when failed_count == 0 AND last_push is not None
- [ ] test_health.py has 3 tests
- [ ] `pytest tests/test_health.py -v` passes (3 tests)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_health.py
import pytest
from src.health import HealthChecker
from src.database import Database
import tempfile
from pathlib import Path

@pytest.fixture
def db():
    """Create temporary database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        database = Database(str(db_path))
        yield database

@pytest.fixture
def health_checker(db):
    return HealthChecker(db)

def test_check_daily_job_empty(health_checker):
    """Test health check - empty database"""
    status = health_checker.check_daily_job()
    assert status["healthy"] is False
    assert status["failed_count"] == 0
    assert status["pushed_today"] == 0
    assert status["last_push"] is None

def test_check_daily_job_with_push(health_checker, db):
    """Test health check - with push record"""
    db.record_pushed(123, "Test Article")
    status = health_checker.check_daily_job()
    assert status["pushed_today"] == 1
    assert status["last_push"] is not None

def test_check_daily_job_with_failures(health_checker, db):
    """Test health check - with failures"""
    with db.get_connection() as conn:
        conn.execute(
            "INSERT INTO failed_pushes (message, error) VALUES (?, ?)",
            ("Test", "Error")
        )
    status = health_checker.check_daily_job()
    assert status["failed_count"] == 1
    assert status["healthy"] is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_health.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write health.py implementation**

```python
# src/health.py
import logging
from src.database import Database

logger = logging.getLogger(__name__)

class HealthChecker:
    def __init__(self, db: Database):
        self.db = db

    def check_daily_job(self) -> dict:
        """Check daily job health status"""
        with self.db.get_connection() as conn:
            last_push = conn.execute(
                "SELECT pushed_at FROM pushed_articles ORDER BY pushed_at DESC LIMIT 1"
            ).fetchone()

            failed_count = conn.execute(
                "SELECT COUNT(*) FROM failed_pushes WHERE retry_count < 3"
            ).fetchone()[0]

            pushed_today = conn.execute(
                "SELECT COUNT(*) FROM pushed_articles WHERE DATE(pushed_at) = DATE('now')"
            ).fetchone()[0]

        return {
            "last_push": last_push[0] if last_push else None,
            "failed_count": failed_count,
            "pushed_today": pushed_today,
            "healthy": failed_count == 0 and last_push is not None
        }

    def log_health_status(self):
        """Output health status log"""
        status = self.check_daily_job()
        if status["healthy"]:
            logger.info(f"Health OK | Pushed today: {status['pushed_today']}")
        else:
            logger.warning(
                f"Health Warning | Failed: {status['failed_count']}, "
                f"Last push: {status['last_push']}"
            )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_health.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/health.py tests/test_health.py
git commit -m "feat: add health check module"
```

---

## Task 10: Scheduler Module

**Files:**
- Create: `src/scheduler.py`

**Review Criteria:**
- [ ] scheduler.py has Scheduler class with start() method
- [ ] Scheduler accepts config and job_func in constructor
- [ ] Uses CronTrigger with timezone support
- [ ] Handles KeyboardInterrupt and SystemExit gracefully

- [ ] **Step 1: Write scheduler.py**

```python
# src/scheduler.py
import logging
from typing import Callable
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from src.config import AppConfig

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self, config: AppConfig, job_func: Callable):
        self.config = config
        self.job_func = job_func
        self.scheduler = BlockingScheduler()

    def start(self) -> None:
        """Start scheduler"""
        cron_parts = self.config.scheduler.cron.split()
        trigger = CronTrigger(
            minute=cron_parts[0],
            hour=cron_parts[1],
            day=cron_parts[2],
            month=cron_parts[3],
            day_of_week=cron_parts[4],
            timezone=self.config.scheduler.timezone
        )

        self.scheduler.add_job(
            self.job_func,
            trigger=trigger,
            id="daily_hackernews",
            name="Daily Hacker News Push",
            misfire_grace_time=3600,
            coalesce=True
        )

        logger.info(f"Scheduler started, cron: {self.config.scheduler.cron}")
        job = self.scheduler.get_job("daily_hackernews")
        logger.info(f"Next run: {job.next_run_time}")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped gracefully")
```

- [ ] **Step 2: Commit**

```bash
git add src/scheduler.py
git commit -m "feat: add APScheduler cron wrapper"
```

---

## Task 11: Main Entry Point

**Files:**
- Create: `src/main.py`

**Review Criteria:**
- [ ] main.py has main() function with load_dotenv() call
- [ ] main.py has run_job() with exception handling
- [ ] main.py has timer() context manager for performance tracking
- [ ] main.py orchestrates: fetch -> filter -> format -> push
- [ ] main.py calls health check and retry_failed_async on startup

- [ ] **Step 1: Write main.py**

```python
# src/main.py
import time
import logging
import threading
from contextlib import contextmanager
from typing import Optional
from dotenv import load_dotenv

from src.config import load_config, AppConfig
from src.logging_config import setup_logging
from src.scraper import HackerNewsScraper
from src.filter import NewsFilter
from src.formatter import MessageFormatter
from src.notifier import ServerChanNotifier
from src.database import Database
from src.health import HealthChecker
from src.scheduler import Scheduler

logger = logging.getLogger(__name__)

@contextmanager
def timer(operation: str):
    """Execution time statistics context manager"""
    start = time.time()
    yield
    duration = time.time() - start
    logger.info(f"{operation} completed in {duration:.2f}s")

def run_job() -> None:
    """Single job execution with exception handling"""
    try:
        with timer("Total job"):
            _execute_job()
    except Exception as e:
        logger.exception(f"Job failed: {e}")
        _notify_failure(e)

def _execute_job() -> None:
    """Execute job core logic"""
    config = load_config()
    db = Database(config.database.path)

    stories = _fetch_stories(config)
    filtered = _filter_stories(config, stories, db)

    if not filtered:
        logger.info("No new stories to push")
        return

    _push_stories(config, filtered, db)

def _fetch_stories(config: AppConfig) -> list[dict]:
    """Fetch stage"""
    with timer("Fetch stories"):
        scraper = HackerNewsScraper()
        stories = scraper.fetch_top_stories_sync(config.hackernews.top_stories_limit)
        logger.info(f"Fetched {len(stories)} stories")
        return stories

def _filter_stories(
    config: AppConfig,
    stories: list[dict],
    db: Database
) -> list[dict]:
    """Filter stage"""
    with timer("Filter stories"):
        news_filter = NewsFilter(config.filter)
        pushed_ids = db.get_pushed_ids()
        filtered = news_filter.filter(stories, pushed_ids)
        logger.info(f"After filter: {len(filtered)} stories")
        return filtered

def _push_stories(
    config: AppConfig,
    stories: list[dict],
    db: Database
) -> None:
    """Push stage"""
    with timer("Push stories"):
        formatter = MessageFormatter()
        message = formatter.format(stories)

        notifier = ServerChanNotifier(config.serverchan.send_key, db)
        title = f"Hacker News 早报 ({len(stories)} 条)"

        if notifier.send(title, message):
            for story in stories:
                db.record_pushed(story["id"], story["title"])
            logger.info(f"Pushed {len(stories)} stories successfully")
        else:
            logger.error("Push failed, will retry next time")

def _notify_failure(error: Exception) -> None:
    """Failure notification"""
    logger.error(f"Job failed: {error}")

def retry_failed_async(config: AppConfig, db: Database) -> None:
    """Async retry failed records (non-blocking)"""
    def _retry():
        notifier = ServerChanNotifier(config.serverchan.send_key, db)
        notifier.retry_failed()
        logger.info("Retry failed pushes completed")

    thread = threading.Thread(target=_retry, daemon=True)
    thread.start()

def main() -> None:
    """Main function"""
    load_dotenv()
    config = load_config()
    setup_logging(config.logging.dict())

    logger.info("Hacker News Agent starting...")

    db = Database(config.database.path)

    # Health check
    health = HealthChecker(db)
    health.log_health_status()

    # Async retry failed records
    retry_failed_async(config, db)

    # Start scheduler
    scheduler = Scheduler(config, run_job)
    scheduler.start()

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add src/main.py
git commit -m "feat: add main entry point with orchestration"
```

---

## Task 12: Run All Tests

**Review Criteria:**
- [ ] `pytest tests/ -v` passes all 37 tests
- [ ] No test failures
- [ ] No regressions from previous tasks

- [ ] **Step 1: Run complete test suite**

```bash
pytest tests/ -v
```

Expected: 37 passed

- [ ] **Step 2: Verify no regressions**

```bash
pytest tests/ --tb=short
```

Expected: All tests pass

- [ ] **Step 3: Commit test results**

```bash
git add .
git commit -m "test: verify all 37 tests pass"
```

---

## Task 13: Documentation

**Files:**
- Create: `README.md`

**Review Criteria:**
- [ ] README.md contains: project description, features, tech stack, quick start, configuration, project structure, deployment, development
- [ ] README.md is in English
- [ ] README.md includes code examples

- [ ] **Step 1: Create README.md**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add comprehensive README"
```

---

## Task 14: Deployment Configuration

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `config/hackernews.service`
- Create: `deploy.sh`

**Review Criteria:**
- [ ] Dockerfile uses python:3.11-slim base image
- [ ] docker-compose.yml mounts config, data, logs volumes
- [ ] docker-compose.yml uses env_file for .env
- [ ] hackernews.service has proper systemd configuration
- [ ] deploy.sh is executable and contains deployment steps

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data logs

CMD ["python", "-m", "src.main"]
```

- [ ] **Step 2: Create docker-compose.yml**

```yaml
version: '3.8'

services:
  hackernews:
    build: .
    container_name: hackernews-agent
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

- [ ] **Step 3: Create systemd service**

```ini
# config/hackernews.service
[Unit]
Description=Hacker News Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/hacker-news-agent
ExecStart=/opt/hacker-news-agent/venv/bin/python -m src.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 4: Create deploy.sh**

```bash
#!/bin/bash
set -e

echo "=== Hacker News Agent Deployment ==="

# 1. Install dependencies
sudo apt update
sudo apt install -y python3.11 python3.11-venv

# 2. Clone project
sudo git clone <your-repo> /opt/hacker-news-agent
sudo chown -R $USER:$USER /opt/hacker-news-agent

cd /opt/hacker-news-agent

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
echo "Please edit .env to add your Server酱 SendKey"

# 6. Create systemd service
sudo cp config/hackernews.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hackernews
sudo systemctl start hackernews

echo "=== Deployment Complete ==="
echo "Check status: sudo systemctl status hackernews"
echo "View logs: sudo journalctl -u hackernews -f"
```

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml config/hackernews.service deploy.sh
git commit -m "feat: add Docker and systemd deployment configs"
```

---

## Task 15: Final Verification

**Review Criteria:**
- [ ] All 37 tests pass
- [ ] All source files exist in src/
- [ ] All test files exist in tests/
- [ ] No uncommitted changes
- [ ] Project structure matches plan

- [ ] **Step 1: Run all tests one final time**

```bash
pytest tests/ -v --tb=short
```

Expected: 37 passed

- [ ] **Step 2: Verify project structure**

```bash
find . -type f -name "*.py" | sort
```

Expected: All source and test files present

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "chore: final project verification"
```

---

## Summary

| Task | Description | Files | Tests |
|------|-------------|-------|-------|
| 1 | Project Scaffolding | 5 | - |
| 2 | Configuration Module | 3 | 5 |
| 3 | Logging Module | 1 | - |
| 4 | Database Module | 2 | 7 |
| 5 | Scraper Module | 2 | 4 |
| 6 | Filter Module | 2 | 8 |
| 7 | Formatter Module | 2 | 5 |
| 8 | Notifier Module | 2 | 5 |
| 9 | Health Check Module | 2 | 3 |
| 10 | Scheduler Module | 1 | - |
| 11 | Main Entry Point | 1 | - |
| 12 | Run All Tests | - | 37 |
| 13 | Documentation | 1 | - |
| 14 | Deployment Config | 4 | - |
| 15 | Final Verification | - | 37 |

**Total:** 28 files, 37 tests
