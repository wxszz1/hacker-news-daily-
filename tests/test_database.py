import pytest
import tempfile
from pathlib import Path
from src.database import Database

@pytest.fixture
def db():
    """创建临时数据库"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        database = Database(str(db_path))
        yield database

def test_database_init(db):
    """测试数据库初始化"""
    assert db.db_path.exists()

def test_get_pushed_ids_empty(db):
    """测试获取已推送 ID - 空数据库"""
    ids = db.get_pushed_ids()
    assert ids == set()

def test_record_pushed(db):
    """测试记录已推送"""
    db.record_pushed(123, "Test Article")
    ids = db.get_pushed_ids()
    assert 123 in ids

def test_record_pushed_duplicate(db):
    """测试记录重复已推送"""
    db.record_pushed(123, "Test Article")
    db.record_pushed(123, "Test Article Again")
    ids = db.get_pushed_ids()
    assert len(ids) == 1

def test_get_pushed_ids_multiple(db):
    """测试获取多个已推送 ID"""
    db.record_pushed(123, "Article 1")
    db.record_pushed(456, "Article 2")
    db.record_pushed(789, "Article 3")
    ids = db.get_pushed_ids()
    assert ids == {123, 456, 789}

def test_database_context_manager(db):
    """测试数据库上下文管理器"""
    with db.get_connection() as conn:
        conn.execute("SELECT 1")
    # 应该正常提交，不抛出异常

def test_database_rollback(db):
    """测试数据库回滚"""
    try:
        with db.get_connection() as conn:
            conn.execute("INSERT INTO pushed_articles (article_id, title) VALUES (1, 'Test')")
            raise Exception("Simulated error")
    except Exception:
        pass

    ids = db.get_pushed_ids()
    assert 1 not in ids
