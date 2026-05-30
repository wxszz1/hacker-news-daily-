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

@patch('src.notifier.time.sleep')
@patch('src.notifier.httpx.post')
def test_retry_failed(mock_post, mock_sleep, notifier):
    """测试重试失败推送"""
    # First, record some failures
    notifier._record_failure("Title 1", "Content 1")
    notifier._record_failure("Title 2", "Content 2")

    # Mock successful response for retry
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    # Retry failed pushes
    notifier.retry_failed()

    # Verify send was called twice (once per failure)
    assert mock_post.call_count == 2

    # Verify all failures were deleted from database
    with notifier.db.get_connection() as conn:
        failures = conn.execute("SELECT * FROM failed_pushes").fetchall()
        assert len(failures) == 0

@patch('src.notifier.time.sleep')
@patch('src.notifier.httpx.post')
def test_retry_failed_partial_failure(mock_post, mock_sleep, notifier):
    """测试部分重试失败"""
    # Record failures
    notifier._record_failure("Title 1", "Content 1")
    notifier._record_failure("Title 2", "Content 2")

    # Mock: first call succeeds, then 3 retries all fail
    success_response = Mock()
    success_response.status_code = 200
    fail_response = Mock()
    fail_response.status_code = 500

    mock_post.side_effect = [success_response, fail_response, fail_response, fail_response]

    # Retry failed pushes
    notifier.retry_failed()

    # Verify: 1 success call + 3 retry calls = 4 total
    assert mock_post.call_count == 4

    # Verify Title 1 was deleted (success) and Title 2 has retry_count incremented
    # Note: when send() fails all retries, _record_failure creates a new record,
    # so we get the original (retry_count=1) plus a new one (retry_count=0)
    with notifier.db.get_connection() as conn:
        failures = conn.execute("SELECT * FROM failed_pushes").fetchall()
        assert len(failures) == 2
        # Verify the original Title 2 failure was updated with retry_count=1
        original = [f for f in failures if f[1] == "Title 2\nContent 2" and f[4] == 1]
        assert len(original) == 1
        # Verify a new record was created for the re-failed push
        new_record = [f for f in failures if f[1] == "Title 2\nContent 2" and f[4] == 0]
        assert len(new_record) == 1

def test_init_validation():
    """测试初始化验证"""
    db = Mock()
    with pytest.raises(ValueError, match="send_key must be a non-empty string"):
        ServerChanNotifier("", db)
    with pytest.raises(ValueError, match="send_key must be a non-empty string"):
        ServerChanNotifier(None, db)
    with pytest.raises(ValueError, match="db cannot be None"):
        ServerChanNotifier("test_key", None)

def test_send_validation(notifier):
    """测试发送验证"""
    with pytest.raises(ValueError, match="title must be a non-empty string"):
        notifier.send("", "content")
    with pytest.raises(ValueError, match="title must be a non-empty string"):
        notifier.send(None, "content")
    with pytest.raises(ValueError, match="content must be a non-empty string"):
        notifier.send("title", "")
    with pytest.raises(ValueError, match="content must be a non-empty string"):
        notifier.send("title", None)
