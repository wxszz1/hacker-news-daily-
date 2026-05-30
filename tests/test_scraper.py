import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
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

@patch('src.scraper.time.sleep')
@patch('src.scraper.httpx.Client')
def test_fetch_top_stories_sync(mock_client_cls, mock_sleep):
    """测试同步获取 top stories 公共方法"""
    scraper = HackerNewsScraper()

    # Mock ID list response
    ids_response = Mock()
    ids_response.json.return_value = [101, 102, 103]
    ids_response.raise_for_status = Mock()

    # Mock story detail responses
    story_responses = []
    for sid in [101, 102, 103]:
        resp = Mock()
        resp.json.return_value = {"id": sid, "title": f"Story {sid}", "score": 50}
        resp.raise_for_status = Mock()
        story_responses.append(resp)

    mock_client = Mock()
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client.get.side_effect = [ids_response] + story_responses
    mock_client_cls.return_value = mock_client

    results = scraper.fetch_top_stories_sync(limit=3)

    assert len(results) == 3
    assert results[0]["id"] == 101
    assert results[2]["id"] == 103

@patch('src.scraper.time.sleep')
@patch('src.scraper.httpx.Client')
def test_fetch_top_stories_sync_limit_none(mock_client_cls, mock_sleep):
    """测试同步获取 top stories 时 limit 为 None 回退默认值"""
    scraper = HackerNewsScraper()
    results = scraper.fetch_top_stories_sync(limit=None)
    assert results == []

@patch('src.scraper.asyncio.sleep', new_callable=AsyncMock)
@patch('src.scraper.httpx.AsyncClient')
@pytest.mark.asyncio
async def test_fetch_top_stories_async(mock_async_client_cls, mock_sleep):
    """测试异步获取 top stories 公共方法"""
    scraper = HackerNewsScraper()

    # Mock ID list response (Mock not AsyncMock - resp.json() is not awaited)
    ids_response = Mock()
    ids_response.json.return_value = [201, 202]
    ids_response.raise_for_status = Mock()

    # Mock story detail responses
    story_resp_1 = Mock()
    story_resp_1.json.return_value = {"id": 201, "title": "Async Story 1", "score": 80}
    story_resp_1.raise_for_status = Mock()

    story_resp_2 = Mock()
    story_resp_2.json.return_value = {"id": 202, "title": "Async Story 2", "score": 90}
    story_resp_2.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get.side_effect = [ids_response, story_resp_1, story_resp_2]

    mock_async_client_cls.return_value.__aenter__.return_value = mock_client
    mock_async_client_cls.return_value.__aexit__.return_value = False

    results = await scraper.fetch_top_stories(limit=2)

    assert len(results) == 2
    assert results[0]["id"] == 201
    assert results[1]["id"] == 202

@patch('src.scraper.asyncio.sleep', new_callable=AsyncMock)
@patch('src.scraper.httpx.AsyncClient')
@pytest.mark.asyncio
async def test_fetch_top_stories_async_limit_none(mock_async_client_cls, mock_sleep):
    """测试异步获取 top stories 时 limit 为 None 回退默认值"""
    scraper = HackerNewsScraper()

    ids_response = Mock()
    ids_response.json.return_value = []
    ids_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get.return_value = ids_response

    mock_async_client_cls.return_value.__aenter__.return_value = mock_client
    mock_async_client_cls.return_value.__aexit__.return_value = False

    results = await scraper.fetch_top_stories(limit=None)
    assert results == []
