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
    """测试按分数过滤"""
    stories = [
        {"id": 1, "title": "AI News", "score": 100},
        {"id": 2, "title": "Low Score", "score": 30},
        {"id": 3, "title": "High Score", "score": 60},
    ]
    result = news_filter._filter_by_score(stories)
    assert len(result) == 2
    assert all(s["score"] >= 50 for s in result)

def test_filter_by_keywords(news_filter):
    """测试按关键词过滤"""
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
    """测试排除关键词"""
    stories = [
        {"id": 1, "title": "AI News", "score": 100},
        {"id": 2, "title": "Who is hiring?", "score": 100},
        {"id": 3, "title": "Python tips", "score": 100},
    ]
    result = news_filter._exclude_by_keywords(stories)
    assert len(result) == 2
    assert not any("hiring" in s["title"].lower() for s in result)

def test_deduplicate(news_filter):
    """测试去重"""
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
    """测试完整过滤流程"""
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
    """测试空输入"""
    result = news_filter.filter([], set())
    assert result == []

def test_filter_no_keyword_match():
    """测试没有关键词匹配时不推送"""
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
    # 没有关键词匹配，应该返回空列表
    assert len(result) == 0
