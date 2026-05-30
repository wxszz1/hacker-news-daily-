import pytest
import tempfile
import os
from pathlib import Path
from src.config import load_config, AppConfig, FilterConfig

def test_load_config_success():
    """测试成功加载配置"""
    config = load_config("config/config.yaml")
    assert isinstance(config, AppConfig)
    assert config.hackernews.top_stories_limit == 30
    assert config.filter.min_score == 50
    assert "ai" in config.filter.keywords

def test_load_config_missing_file():
    """测试配置文件不存在"""
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent.yaml")

def test_filter_config_validation():
    """测试过滤配置校验"""
    config = FilterConfig(min_score=100, keywords=["test"])
    assert config.min_score == 100
    assert config.keywords == ["test"]

def test_filter_config_empty_keywords():
    """测试空关键词校验"""
    with pytest.raises(ValueError):
        FilterConfig(keywords=[])

def test_filter_config_keywords_lowercase():
    """测试关键词自动转小写"""
    config = FilterConfig(keywords=["AI", "LLM", "Python"])
    assert config.keywords == ["ai", "llm", "python"]
