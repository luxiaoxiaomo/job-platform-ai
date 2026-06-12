"""
RateLimiterV2单元测试（使用fakeredis，不依赖真实Redis）
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from app.utils.rate_limiter_v2 import RateLimiterV2, build_sms_rate_limit_keys


@pytest_asyncio.fixture
async def mock_redis():
    """Mock redis客户端，模拟Lua脚本执行"""
    mock = AsyncMock()

    # 模拟Lua脚本返回值
    # [allowed, remaining/ttl]
    mock.eval = AsyncMock(return_value=[1, 2])  # 默认允许，剩余2次

    return mock


@pytest.mark.asyncio
async def test_rate_limiter_first_request():
    """测试首次请求"""
    with patch('app.utils.rate_limiter_v2.redis_client') as mock_client:
        mock_client.redis.eval = AsyncMock(return_value=[1, 2])

        allowed, remaining = await RateLimiterV2.check_rate_limit(
            "test:key:1", 3, 60
        )

        assert allowed is True
        assert remaining == 2


@pytest.mark.asyncio
async def test_rate_limiter_exceed_limit():
    """测试超过限制"""
    with patch('app.utils.rate_limiter_v2.redis_client') as mock_client:
        # 返回拒绝+TTL
        mock_client.redis.eval = AsyncMock(return_value=[0, 58])

        allowed, ttl = await RateLimiterV2.check_rate_limit(
            "test:key:2", 3, 60
        )

        assert allowed is False
        assert ttl == 58


@pytest.mark.asyncio
async def test_rate_limiter_multi_dimension_all_pass():
    """测试多维度限流：全部通过"""
    with patch('app.utils.rate_limiter_v2.redis_client') as mock_client:
        mock_client.redis.eval = AsyncMock(return_value=[1, 1])

        dimensions = [
            ("test:phone:1", 2, 60),
            ("test:ip:1", 5, 60),
        ]

        allowed, rejected_key, info = await RateLimiterV2.check_multi_dimension(
            dimensions, fail_open=False
        )

        assert allowed is True
        assert rejected_key is None


@pytest.mark.asyncio
async def test_rate_limiter_multi_dimension_phone_blocked():
    """测试多维度限流：手机号维度被拒"""
    with patch('app.utils.rate_limiter_v2.redis_client') as mock_client:
        # 第一次调用拒绝
        mock_client.redis.eval = AsyncMock(return_value=[0, 55])

        dimensions = [
            ("test:phone:2", 1, 60),
        ]

        # 被拒
        allowed, rejected_key, ttl = await RateLimiterV2.check_multi_dimension(dimensions)
        assert allowed is False
        assert rejected_key == "test:phone:2"
        assert ttl == 55


@pytest.mark.asyncio
async def test_build_sms_rate_limit_keys():
    """测试短信限流键构建"""
    phone = "13800138000"
    ip = "192.168.1.1"

    dimensions = build_sms_rate_limit_keys(phone, ip)

    # 应该有5个维度：3个手机号 + 2个IP
    assert len(dimensions) == 5

    # 检查手机号维度
    phone_keys = [d[0] for d in dimensions if ":phone:" in d[0]]
    assert len(phone_keys) == 3

    # 检查IP维度
    ip_keys = [d[0] for d in dimensions if ":ip:" in d[0]]
    assert len(ip_keys) == 2


@pytest.mark.asyncio
async def test_build_sms_rate_limit_keys_no_ip():
    """测试短信限流键构建（无IP）"""
    phone = "13800138000"

    dimensions = build_sms_rate_limit_keys(phone, ip=None)

    # 只有手机号维度
    assert len(dimensions) == 3
    assert all(":phone:" in d[0] for d in dimensions)


@pytest.mark.asyncio
async def test_rate_limiter_fail_closed():
    """测试fail_closed模式（Redis异常时拒绝）"""
    with patch('app.utils.rate_limiter_v2.redis_client') as mock_client:
        mock_client.redis.eval = AsyncMock(side_effect=Exception("Redis error"))

        allowed, info = await RateLimiterV2.check_rate_limit(
            "test:key:3", 3, 60, fail_open=False
        )

        assert allowed is False
        assert info == 0


@pytest.mark.asyncio
async def test_rate_limiter_fail_open():
    """测试fail_open模式（Redis异常时放行）"""
    with patch('app.utils.rate_limiter_v2.redis_client') as mock_client:
        mock_client.redis.eval = AsyncMock(side_effect=Exception("Redis error"))

        allowed, remaining = await RateLimiterV2.check_rate_limit(
            "test:key:4", 3, 60, fail_open=True
        )

        assert allowed is True
        assert remaining == 3  # 返回max_requests
