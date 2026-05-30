import pytest
from datetime import datetime, timedelta
from src.formatter import MessageFormatter

@pytest.fixture
def formatter():
    return MessageFormatter()

def test_format_stories(formatter):
    """测试格式化故事"""
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
    """测试格式化空故事列表"""
    result = formatter.format([])
    assert result is None

def test_format_age_hours(formatter):
    """测试格式化时间 - 小时"""
    timestamp = int(datetime.now().timestamp()) - 3600  # 1小时前
    result = formatter._format_age(timestamp)
    assert "h ago" in result

def test_format_age_days(formatter):
    """测试格式化时间 - 天"""
    timestamp = int(datetime.now().timestamp()) - 86400 * 2  # 2天前
    result = formatter._format_age(timestamp)
    assert "d ago" in result

def test_format_no_url(formatter):
    """测试没有 URL 的故事"""
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
