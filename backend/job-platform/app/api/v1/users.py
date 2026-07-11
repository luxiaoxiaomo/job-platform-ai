"""
用户管理API：获取、更新用户信息
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.user.models import User
from app.modules.user.schemas import UserListResponse, UserResponse, UserUpdate
from app.modules.user.service import UserService
from app.utils.encryption import encryptor

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户信息

    需要在请求Header中携带Token：
    ```
    Authorization: Bearer <access_token>
    ```
    """
    return UserResponse(
        id=current_user.id,
        phone=encryptor.decrypt(current_user.phone_encrypted),
        display_name=current_user.display_name,
        role=current_user.role,
        avatar_url=current_user.avatar_url,
        status=current_user.status,
        created_at=current_user.created_at
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前登录用户信息

    可更新字段：
    - **display_name**: 显示名称
    - **avatar_url**: 头像URL
    - **real_name**: 真实姓名（加密存储）
    """
    updated_user = await UserService.update_profile(db, current_user.id, data)

    return UserResponse(
        id=updated_user.id,
        phone=encryptor.decrypt(updated_user.phone_encrypted),
        display_name=updated_user.display_name,
        role=updated_user.role,
        avatar_url=updated_user.avatar_url,
        status=updated_user.status,
        created_at=updated_user.created_at
    )


@router.get("/admin", response_model=UserListResponse)
async def list_users_for_admin(
    role: Optional[str] = Query(None, description="seeker/recruiter/admin"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin user list for resource management."""
    return await UserService.list_for_admin(db, current_user, skip=skip, limit=limit, role=role)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定用户信息（需要权限）

    权限规则：
    - 仅本人或管理员可以访问完整用户信息（包含手机号）
    - 其他用户访问会返回403错误

    - **user_id**: 用户ID
    """
    # 权限检查：仅本人或admin可访问
    if user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该用户信息"
        )

    user = await UserService.get_user_info(db, user_id)

    return UserResponse(
        id=user.id,
        phone=encryptor.decrypt(user.phone_encrypted),
        display_name=user.display_name,
        role=user.role,
        avatar_url=user.avatar_url,
        status=user.status,
        created_at=user.created_at
    )
