"""
全局依赖注入：数据库会话、当前用户认证
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db

# HTTP Bearer Token认证
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    从JWT Token获取当前用户

    Args:
        credentials: HTTP Authorization Header中的Token
        db: 数据库会话

    Returns:
        当前用户对象

    Raises:
        HTTPException: Token无效或用户不存在
    """
    token = credentials.credentials

    # 解码Token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[int] = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 从数据库查询用户
    from app.modules.user.repository import UserRepository

    user = await UserRepository.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户状态
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"用户账号已{user.status}",
        )

    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: AsyncSession = Depends(get_db),
):
    """Return the current user when a valid bearer token is present, otherwise None."""
    if credentials is None:
        return None

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        return None

    user_id: Optional[int] = payload.get("user_id")
    if user_id is None:
        return None

    from app.modules.user.repository import UserRepository

    user = await UserRepository.get_by_id(db, user_id)
    if user is None or user.status != "active":
        return None
    return user


def require_role(*allowed_roles: str):
    """
    角色权限验证装饰器工厂

    Args:
        *allowed_roles: 允许的角色列表

    Returns:
        依赖函数

    Example:
        @router.get("/admin/users", dependencies=[Depends(require_role("admin"))])
        async def list_users(): ...
    """
    async def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要{'/'.join(allowed_roles)}角色权限",
            )
        return current_user

    return role_checker
