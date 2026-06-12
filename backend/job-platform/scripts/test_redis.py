import asyncio
from app.utils.redis_client import redis_client


async def test_redis():
    try:
        result = await redis_client.redis.ping()
        print(f"✓ Redis PING: {result}")

        # 测试设置验证码
        await redis_client.set_verification_code("test_phone", "123456", 300)
        print("✓ Set verification code success")

        # 测试验证验证码
        is_valid = await redis_client.verify_code("test_phone", "123456")
        print(f"✓ Verify code result: {is_valid}")

        print("\nRedis connection is working!")

    except Exception as e:
        print(f"✗ Redis error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_redis())
