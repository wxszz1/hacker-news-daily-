import pytest
from src.health import HealthChecker
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
def health_checker(db):
    return HealthChecker(db)

def test_check_daily_job_empty(health_checker):
    """测试健康检查 - 空数据库"""
    status = health_checker.check_daily_job()
    assert status["healthy"] is False
    assert status["failed_count"] == 0
    assert status["pushed_today"] == 0
    assert status["last_push"] is None

def test_check_daily_job_with_push(health_checker, db):
    """测试健康检查 - 有推送记录"""
    db.record_pushed(123, "Test Article")
    status = health_checker.check_daily_job()
    assert status["pushed_today"] == 1
    assert status["last_push"] is not None

def test_check_daily_job_with_failures(health_checker, db):
    """测试健康检查 - 有失败记录"""
    with db.get_connection() as conn:
        conn.execute(
            "INSERT INTO failed_pushes (message, error) VALUES (?, ?)",
            ("Test", "Error")
        )
    status = health_checker.check_daily_job()
    assert status["failed_count"] == 1
    assert status["healthy"] is False
