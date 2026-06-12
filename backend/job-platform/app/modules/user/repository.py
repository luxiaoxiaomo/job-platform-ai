"""
User Repository - 数据访问层
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.models import User


class UserRepository:
    """用户数据访问层"""

    @staticmethod
    async def create(db: AsyncSession, user: User) -> User:
        """
        创建用户

        Args:
            db: 数据库会话
            user: 用户对象

        Returns:
            创建的用户
        """
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """
        根据ID查询用户

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            用户对象，不存在返回None
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_phone_hash(db: AsyncSession, phone_hash: str) -> Optional[User]:
        """
        根据手机号哈希查询用户（用于注册查重、登录）

        Args:
            db: 数据库会话
            phone_hash: 手机号哈希（HMAC-SHA256）

        Returns:
            用户对象，不存在返回None
        """
        result = await db.execute(
            select(User).where(User.phone_hash == phone_hash)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_phone(db: AsyncSession, phone_encrypted: str) -> Optional[User]:
        """
        根据加密手机号查询用户（已废弃，请使用get_by_phone_hash）

        Args:
            db: 数据库会话
            phone_encrypted: 加密的手机号

        Returns:
            用户对象，不存在返回None
        """
        result = await db.execute(
            select(User).where(User.phone_encrypted == phone_encrypted)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(db: AsyncSession, user: User) -> User:
        """
        更新用户

        Args:
            db: 数据库会话
            user: 用户对象

        Returns:
            更新后的用户
        """
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def list(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        role: Optional[str] = None
    ) -> List[User]:
        """
        查询用户列表

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 限制记录数
            role: 角色筛选（可选）

        Returns:
            用户列表
        """
        query = select(User)

        if role:
            query = query.where(User.role == role)

        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()
