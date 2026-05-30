import pytest
from unittest.mock import Mock, patch, MagicMock
from src.notifier import ServerChanNotifier
from src.database import Database
import tempfile
from pathlib import Path

@pytest.fixture
def db():
    """创建临时数据库"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        database = Database(str(db_path))
        yield database

@pytest.fixture
def notifier(db):
    return ServerChanNotifier("test_send_key", db)

@patch('src.notifier.httpx.post')
def test_send_success(mock_post, notifier):
    """测试推送成功"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result = notifier.send("Test Title", "Test Content")
    assert result is True

@patch('src.notifier.httpx.post')
def test_send_failure(mock_post, notifier):
    """测试推送失败"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response

    result = notifier.send("Test Title", "Test Content")
    assert result is False

@patch('src.notifier.httpx.post')
def test_send_exception(mock_post, notifier):
    """测试推送异常"""
    mock_post.side_effect = Exception("Network error")

    result = notifier.send("Test Title", "Test Content")
    assert result is False

@patch('src.notifier.httpx.post')
def test_send_retry(mock_post, notifier):
    """测试推送重试"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response

    notifier.send("Test Title", "Test Content")
    # 应该重试 3 次
    assert mock_post.call_count == 3

def test_record_failure(notifier):
    """测试记录失败"""
    notifier._record_failure("Test Title", "Test Content")

    with notifier.db.get_connection() as conn:
        failures = conn.execute("SELECT * FROM failed_pushes").fetchall()
        assert len(failures) == 1
