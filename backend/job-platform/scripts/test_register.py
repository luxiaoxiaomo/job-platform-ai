import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.modules.user.models import User
from app.modules.user.service import UserService
from app.modules.user.schemas import UserRegister
from app.utils.redis_client import redis_client


async def test_register():
    print("=== Testing Registration Flow ===\n")

    # 1. 设置验证码
    phone = "13600136000"
    code = "123456"

    print(f"1. Setting verification code for {phone}...")
    await redis_client.set_verification_code(phone, code, 300)
    print("   OK\n")

    # 2. 创建数据库会话
    print("2. Creating database session...")
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        print("   OK\n")

        # 3. 注册用户
        print("3. Registering user...")
        try:
            user_data = UserRegister(
                phone=phone,
                password="Test1234",
                display_name="TestUser",
                role="seeker",
                verification_code=code
            )

            user = await UserService.register(db, user_data)
            print(f"   SUCCESS!")
            print(f"   UserID: {user.id}")
            print(f"   Role: {user.role}")
            print(f"   Status: {user.status}")

        except Exception as e:
            print(f"   FAILED: {e}")
            import traceback
            traceback.print_exc()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_register())
