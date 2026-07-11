"""
限流工具：基于Redis的频率限制
"""
from app.utils.redis_client import redis_client


class RateLimiter:
    """基于Redis的限流器"""

    @staticmethod
    async def check_rate_limit(
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        检查是否超过频率限制

        Args:
            key: 限流键（例如：rate_limit:sms:13800138000）
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）

        Returns:
            (是否允许, 剩余请求次数)
        """
        try:
            # 获取当前请求次数
            current = await redis_client.redis.get(key)

            if current is None:
                # 首次请求，设置为1并设置过期时间
                await redis_client.redis.setex(key, window_seconds, 1)
                return True, max_requests - 1

            current_count = int(current)

            if current_count >= max_requests:
                # 超过限制
                return False, 0

            # 未超过限制，递增计数
            await redis_client.redis.incr(key)
            return True, max_requests - current_count - 1

        except Exception as e:
            # Redis失败时不阻止请求（降级策略）
            print(f"限流检查失败: {e}")
            return True, max_requests

    @staticmethod
    async def get_remaining_ttl(key: str) -> int:
        """
        获取限流键的剩余TTL

        Args:
            key: 限流键

        Returns:
            剩余秒数，-1表示键不存在
        """
        try:
            ttl = await redis_client.redis.ttl(key)
            return ttl if ttl > 0 else 0
        except Exception:
            return 0


# 预定义限流规则
SMS_RATE_LIMITS = {
    "per_minute": (1, 60),      # 每分钟1次
    "per_hour": (3, 3600),       # 每小时3次
    "per_day": (10, 86400),      # 每天10次
}
