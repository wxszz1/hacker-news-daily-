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
    """获取项目根目录"""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "config").exists() and (current / "src").exists():
            return current
        current = current.parent
    return Path(__file__).parent.parent

def load_config(config_path: str = None) -> AppConfig:
    """加载并校验配置文件"""
    project_root = get_project_root()

    if config_path is None:
        config_path = project_root / "config" / "config.yaml"

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # 处理数据库和日志路径，使用绝对路径
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
