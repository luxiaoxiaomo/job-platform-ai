"""
手机号哈希工具：确定性哈希，用于查询和唯一性检查
"""
import hmac
import hashlib

from app.core.config import settings


def hash_phone(phone: str) -> str:
    """
    对手机号进行确定性哈希（HMAC-SHA256）

    用于：
    - 数据库查询（phone_hash字段）
    - 唯一性检查
    - 注册时查重
    - 登录时查找用户

    Args:
        phone: 手机号明文（需要先规范化，如去除空格、+86等）

    Returns:
        64位十六进制哈希字符串
    """
    # 规范化手机号（去除空格、短横线等）
    normalized_phone = phone.strip().replace(" ", "").replace("-", "")

    # 使用HMAC-SHA256进行确定性哈希
    # 使用独立的PHONE_HASH_SECRET，不复用JWT_SECRET_KEY
    hash_secret = settings.PHONE_HASH_SECRET.encode('utf-8')
    phone_bytes = normalized_phone.encode('utf-8')

    phone_hash = hmac.new(
        hash_secret,
        phone_bytes,
        hashlib.sha256
    ).hexdigest()

    return phone_hash
