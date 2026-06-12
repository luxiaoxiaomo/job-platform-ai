"""
Redis客户端工具：验证码存储和验证
"""
import random
from typing import Optional
import redis.asyncio as redis

from app.core.config import settings


class RedisClient:
    """Redis客户端封装"""

    def __init__(self):
        """初始化Redis连接"""
        self.redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

    async def set_verification_code(self, phone: str, code: str, ttl: int = 300) -> bool:
        """
        存储验证码

        Args:
            phone: 手机号
            code: 验证码
            ttl: 过期时间（秒），默认5分钟

        Returns:
            是否成功
        """
        key = f"verification_code:{phone}"
        try:
            await self.redis.setex(key, ttl, code)
            return True
        except Exception as e:
            print(f"Redis存储验证码失败: {e}")
            return False

    async def verify_code(self, phone: str, code: str) -> bool:
        """
        验证验证码

        Args:
            phone: 手机号
            code: 用户输入的验证码

        Returns:
            验证码是否正确
        """
        key = f"verification_code:{phone}"
        try:
            stored_code = await self.redis.get(key)
            if stored_code and stored_code == code:
                # 验证成功后删除验证码（防止重复使用）
                await self.redis.delete(key)
                return True
            return False
        except Exception as e:
            print(f"Redis验证验证码失败: {e}")
            return False

    async def get_code(self, phone: str) -> Optional[str]:
        """
        获取验证码（开发环境用于测试）

        Args:
            phone: 手机号

        Returns:
            验证码，不存在返回None
        """
        key = f"verification_code:{phone}"
        try:
            return await self.redis.get(key)
        except Exception as e:
            print(f"Redis获取验证码失败: {e}")
            return None

    @staticmethod
    def generate_code(length: int = 6) -> str:
        """
        生成随机验证码

        Args:
            length: 验证码长度，默认6位

        Returns:
            验证码字符串
        """
        return "".join([str(random.randint(0, 9)) for _ in range(length)])

    async def close(self):
        """关闭Redis连接"""
        await self.redis.close()


# 全局Redis客户端实例
redis_client = RedisClient()
