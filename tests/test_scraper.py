import pytest
from unittest.mock import Mock, patch, MagicMock
from src.scraper import HackerNewsScraper

def test_scraper_init():
    """测试爬虫初始化"""
    scraper = HackerNewsScraper()
    assert scraper.BASE_URL == "https://hacker-news.firebaseio.com/v0"
    assert scraper.REQUEST_DELAY == 0.1
    assert scraper.TIMEOUT == 10.0

@patch('src.scraper.httpx.Client')
def test_fetch_ids_sync_success(mock_client):
    """测试同步获取 ID 列表"""
    mock_response = Mock()
    mock_response.json.return_value = [123, 456, 789]
    mock_response.raise_for_status = Mock()
    mock_client.return_value.__enter__.return_value.get.return_value = mock_response

    scraper = HackerNewsScraper()
    ids = scraper._fetch_ids_sync(mock_client.return_value.__enter__.return_value, "topstories")

    assert ids == [123, 456, 789]

@patch('src.scraper.httpx.Client')
def test_fetch_ids_sync_failure(mock_client):
    """测试同步获取 ID 列表失败"""
    mock_client.return_value.__enter__.return_value.get.side_effect = Exception("Network error")

    scraper = HackerNewsScraper()
    ids = scraper._fetch_ids_sync(mock_client.return_value.__enter__.return_value, "topstories")

    assert ids == []

@patch('src.scraper.httpx.Client')
@patch('src.scraper.time.sleep')
def test_get_story_detail_sync_success(mock_sleep, mock_client):
    """测试同步获取故事详情"""
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
    """测试同步获取故事详情 - 不存在"""
    mock_response = Mock()
    mock_response.json.return_value = None
    mock_response.raise_for_status = Mock()
    mock_client.return_value.__enter__.return_value.get.return_value = mock_response

    scraper = HackerNewsScraper()
    story = scraper._get_story_detail_sync(mock_client.return_value.__enter__.return_value, 999)

    assert story is None
