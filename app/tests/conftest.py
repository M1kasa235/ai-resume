import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import pytest_asyncio
from app.main import app
from app.db.session import get_db
from app.db.base import Base
from app.core.config import settings

# 测试数据库配置
TEST_DATABASE_URL = settings.TEST_DATABASE_URL or "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db():
    """创建测试数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session(test_db):
    """创建数据库会话"""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """创建认证头"""
    return {"Authorization": "Bearer test-token"}