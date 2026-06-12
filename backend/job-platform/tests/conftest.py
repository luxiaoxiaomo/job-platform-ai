"""
测试配置和Fixtures - 使用SQLite避免asyncpg连接池问题
"""
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.engine.url import make_url
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.base import Base
from app.core.config import settings

# 使用SQLite进行测试（避免asyncpg在Windows上的连接池问题）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 安全校验：生产环境必须使用PostgreSQL
if settings.TEST_DATABASE_URL:
    parsed_url = make_url(settings.TEST_DATABASE_URL)
    db_name = parsed_url.database

    if not db_name or not db_name.endswith("_test"):
        raise ValueError(
            f"生产测试数据库名必须以'_test'结尾，当前数据库名: {db_name}\n"
            f"完整URL: {settings.TEST_DATABASE_URL}\n"
            "请在.env中配置: TEST_DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname_test"
        )

# 创建测试引擎（SQLite in-memory）
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

# 创建测试会话工厂
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def setup_database():
    """
    每个测试前创建表，测试后清理表

    注意：不使用autouse，仅在需要数据库的测试中显式使用
    """
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # 清理所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """
    创建测试数据库会话

    依赖setup_database确保表已创建
    """
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    创建测试HTTP客户端
    """
    from app.db.session import get_db

    # 覆盖依赖
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # 创建测试客户端
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    # 清理依赖覆盖
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """测试用户数据"""
    return {
        "phone": "13800138000",
        "password": "Test1234",
        "display_name": "测试用户",
        "role": "seeker",
    }


@pytest.fixture
def test_recruiter_data():
    """测试招聘者数据"""
    return {
        "phone": "13900139000",
        "password": "Recruiter123",
        "display_name": "测试招聘者",
        "role": "recruiter",
    }


@pytest.fixture(autouse=True)
def mock_ocr_provider():
    """Keep API tests deterministic; RapidOCR is covered by parser/provider tests."""
    original_provider = settings.OCR_PROVIDER
    settings.OCR_PROVIDER = "mock"
    yield
    settings.OCR_PROVIDER = original_provider


@pytest.fixture(autouse=True)
def mock_redis():
    """自动Mock Redis（用于所有测试）"""
    from unittest.mock import AsyncMock, patch, MagicMock

    # 创建mock客户端
    mock_client = MagicMock()
    mock_client.redis = AsyncMock()

    # Mock方法
    mock_client.generate_code = MagicMock(return_value="123456")
    mock_client.set_verification_code = AsyncMock(return_value=True)
    mock_client.get_verification_code = AsyncMock(return_value="123456")
    mock_client.verify_code = AsyncMock(return_value=True)
    mock_client.delete_verification_code = AsyncMock(return_value=True)

    # Patch所有使用redis_client的地方
    with patch('app.utils.redis_client.redis_client', mock_client), \
         patch('app.utils.rate_limiter_v2.redis_client', mock_client), \
         patch('app.api.v1.auth.redis_client', mock_client):

        # 默认限流器总是允许
        mock_client.redis.eval = AsyncMock(return_value=[1, 10])
        yield mock_client
