import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(config: dict):
    """配置结构化日志，按天轮转"""
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
