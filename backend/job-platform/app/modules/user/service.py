"""
User Service - 业务逻辑层
"""
from typing import Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.models import User
from app.modules.user.schemas import UserRegister, UserLogin, UserUpdate
from app.modules.user.repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token
from app.utils.encryption import encryptor
from app.utils.phone_hash import hash_phone


class UserService:
    """用户业务逻辑层"""

    @staticmethod
    async def register(db: AsyncSession, data: UserRegister) -> User:
        """
        用户注册

        Args:
            db: 数据库会话
            data: 注册数据

        Returns:
            创建的用户

        Raises:
            HTTPException: 手机号已注册或验证码错误
        """
        # 1. 验证验证码
        from app.utils.redis_client import redis_client
        is_valid = await redis_client.verify_code(data.phone, data.verification_code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误或已过期"
            )

        # 2. 检查手机号是否已注册（使用phone_hash查询）
        phone_hash = hash_phone(data.phone)
        existing_user = await UserRepository.get_by_phone_hash(db, phone_hash)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该手机号已注册"
            )

        # 3. 创建用户
        phone_encrypted = encryptor.encrypt(data.phone)
        user = User(
            phone_hash=phone_hash,
            phone_encrypted=phone_encrypted,
            password_hash=hash_password(data.password),
            display_name=data.display_name,
            role=data.role,
            status="active"
        )

        user = await UserRepository.create(db, user)
        return user

    @staticmethod
    async def login(db: AsyncSession, data: UserLogin) -> Tuple[User, str]:
        """
        用户登录

        Args:
            db: 数据库会话
            data: 登录数据

        Returns:
            (用户对象, JWT Token)

        Raises:
            HTTPException: 手机号或密码错误
        """
        # 1. 使用phone_hash查询用户
        phone_hash = hash_phone(data.phone)
        user = await UserRepository.get_by_phone_hash(db, phone_hash)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="手机号或密码错误"
            )

        # 2. 验证密码
        if not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="手机号或密码错误"
            )

        # 3. 检查用户状态
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"用户账号已{user.status}"
            )

        # 4. 生成JWT Token
        token_data = {
            "user_id": user.id,
            "role": user.role
        }
        access_token = create_access_token(token_data)

        return user, access_token

    @staticmethod
    async def get_user_info(db: AsyncSession, user_id: int) -> User:
        """
        获取用户信息

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            用户对象

        Raises:
            HTTPException: 用户不存在
        """
        user = await UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return user

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        user_id: int,
        data: UserUpdate
    ) -> User:
        """
        更新用户资料

        Args:
            db: 数据库会话
            user_id: 用户ID
            data: 更新数据

        Returns:
            更新后的用户

        Raises:
            HTTPException: 用户不存在
        """
        user = await UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 更新字段
        if data.display_name is not None:
            user.display_name = data.display_name

        if data.avatar_url is not None:
            user.avatar_url = data.avatar_url

        if data.real_name is not None:
            user.real_name_encrypted = encryptor.encrypt(data.real_name)

        user = await UserRepository.update(db, user)
        return user
