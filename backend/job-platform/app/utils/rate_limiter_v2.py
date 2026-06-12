"""
限流工具：基于Redis的频率限制（原子操作版本）
"""
from typing import Optional, Tuple
from app.utils.redis_client import redis_client


class RateLimiterV2:
    """基于Redis原子操作的限流器"""

    # Lua脚本：原子性检查和递增
    LUA_CHECK_AND_INCR = """
    local key = KEYS[1]
    local max_requests = tonumber(ARGV[1])
    local window_seconds = tonumber(ARGV[2])

    local current = redis.call('GET', key)

    if current == false then
        -- 首次请求
        redis.call('SETEX', key, window_seconds, 1)
        return {1, max_requests - 1}
    end

    local current_count = tonumber(current)

    if current_count >= max_requests then
        -- 超过限制
        local ttl = redis.call('TTL', key)
        return {0, ttl}
    end

    -- 未超过限制，递增
    redis.call('INCR', key)
    return {1, max_requests - current_count - 1}
    """

    @classmethod
    async def check_rate_limit(
        cls,
        key: str,
        max_requests: int,
        window_seconds: int,
        fail_open: bool = False
    ) -> Tuple[bool, int]:
        """
        检查是否超过频率限制（原子操作）

        Args:
            key: 限流键
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）
            fail_open: Redis异常时是否放行（默认False，短信场景建议False）

        Returns:
            (是否允许, 剩余信息：允许时返回剩余次数，拒绝时返回剩余TTL秒数)
        """
        try:
            # 使用Lua脚本保证原子性
            result = await redis_client.redis.eval(
                cls.LUA_CHECK_AND_INCR,
                1,  # keys数量
                key,
                max_requests,
                window_seconds
            )

            allowed = bool(result[0])
            info = int(result[1])
            return allowed, info

        except Exception as e:
            # Redis异常处理
            print(f"限流检查失败: {e}")
            if fail_open:
                # fail-open: 允许请求通过
                return True, max_requests
            else:
                # fail-closed: 拒绝请求（更安全，适合短信等场景）
                return False, 0

    @classmethod
    async def check_multi_dimension(
        cls,
        dimensions: list[Tuple[str, int, int]],
        fail_open: bool = False
    ) -> Tuple[bool, Optional[str], int]:
        """
        多维度限流检查（手机号 + IP）

        Args:
            dimensions: [(key, max_requests, window_seconds), ...]
            fail_open: Redis异常时是否放行

        Returns:
            (是否允许, 被拒绝的维度key, 剩余TTL/次数)
        """
        for key, max_req, window in dimensions:
            allowed, info = await cls.check_rate_limit(
                key, max_req, window, fail_open
            )
            if not allowed:
                return False, key, info

        return True, None, 0


# 预定义限流规则
SMS_RATE_LIMITS = {
    "per_minute": (1, 60),      # 每分钟1次
    "per_hour": (3, 3600),       # 每小时3次
    "per_day": (10, 86400),      # 每天10次
}


def build_sms_rate_limit_keys(phone: str, ip: Optional[str] = None) -> list[Tuple[str, int, int]]:
    """
    构建短信验证码限流的多维度键

    Args:
        phone: 手机号
        ip: IP地址（可选）

    Returns:
        [(key, max_requests, window_seconds), ...]
    """
    dimensions = []

    # 手机号维度
    for period, (max_req, window) in SMS_RATE_LIMITS.items():
        key = f"rate_limit:sms:phone:{phone}:{period}"
        dimensions.append((key, max_req, window))

    # IP维度（防止单个IP大量扫号）
    if ip:
        # IP限流：每分钟最多5个不同号码，每小时最多20个
        dimensions.append((f"rate_limit:sms:ip:{ip}:per_minute", 5, 60))
        dimensions.append((f"rate_limit:sms:ip:{ip}:per_hour", 20, 3600))

    return dimensions
