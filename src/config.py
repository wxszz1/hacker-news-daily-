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

def load_config(config_path: str = "config/config.yaml") -> AppConfig:
    """加载并校验配置文件"""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    try:
        return AppConfig(**data)
    except Exception as e:
        raise ValueError(f"Config validation failed: {e}")
