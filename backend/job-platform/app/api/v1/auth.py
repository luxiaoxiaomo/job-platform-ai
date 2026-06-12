"""
认证API：注册、登录、验证码
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.modules.user.schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from app.modules.user.service import UserService
from app.utils.redis_client import redis_client
from app.utils.encryption import encryptor
from app.utils.rate_limiter_v2 import RateLimiterV2, build_sms_rate_limit_keys

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册

    - **phone**: 手机号（11位）
    - **password**: 密码（8-20字符，需包含字母和数字）
    - **display_name**: 显示名称（2-20字符）
    - **role**: 角色（seeker应聘者 / recruiter招聘者）
    - **verification_code**: 验证码（6位数字）
    """
    # 注册用户
    user = await UserService.register(db, data)

    # 生成Token
    from app.core.security import create_access_token
    token_data = {"user_id": user.id, "role": user.role}
    access_token = create_access_token(token_data)

    # 构造响应
    user_response = UserResponse(
        id=user.id,
        phone=encryptor.decrypt(user.phone_encrypted),
        display_name=user.display_name,
        role=user.role,
        avatar_url=user.avatar_url,
        status=user.status,
        created_at=user.created_at
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录

    - **phone**: 手机号（11位）
    - **password**: 密码
    """
    # 登录验证
    user, access_token = await UserService.login(db, data)

    # 构造响应
    user_response = UserResponse(
        id=user.id,
        phone=encryptor.decrypt(user.phone_encrypted),
        display_name=user.display_name,
        role=user.role,
        avatar_url=user.avatar_url,
        status=user.status,
        created_at=user.created_at
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


@router.post("/send-verification-code")
async def send_verification_code(phone: str, request: Request):
    """
    发送验证码（短信）

    - **phone**: 手机号（11位）

    **频率限制（原子操作，多维度）**：
    - 手机号：每分钟1次、每小时3次、每天10次
    - IP：每分钟5个号码、每小时20个号码

    **一期实现**：Mock发送，开发环境返回验证码
    **二期TODO**：集成阿里云/腾讯云短信服务
    """
    # 验证手机号格式
    import re
    if not re.match(r"^1[3-9]\d{9}$", phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号格式不正确"
        )

    # 获取客户端IP
    client_ip = request.client.host if request.client else None

    # 多维度限流检查（手机号 + IP）
    dimensions = build_sms_rate_limit_keys(phone, client_ip)
    allowed, rejected_key, info = await RateLimiterV2.check_multi_dimension(
        dimensions,
        fail_open=False  # 短信场景：Redis异常时拒绝请求
    )

    if not allowed:
        # 解析被拒绝的维度
        if rejected_key and ":ip:" in rejected_key:
            detail = f"该IP请求过于频繁，请{info}秒后重试"
        else:
            detail = f"发送过于频繁，请{info}秒后重试"

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )

    # 生成6位验证码
    code = redis_client.generate_code(6)

    # 存入Redis（5分钟过期）
    success = await redis_client.set_verification_code(phone, code, ttl=300)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证码发送失败，请稍后重试"
        )

    # TODO: 调用短信服务发送验证码
    # 一期Mock：开发环境直接返回验证码
    if settings.ENV == "dev":
        return {
            "message": "验证码发送成功（开发环境）",
            "code": code,  # 仅开发环境返回
            "expires_in": 300  # 5分钟
        }
    else:
        return {
            "message": "验证码已发送，请注意查收短信",
            "expires_in": 300
        }
