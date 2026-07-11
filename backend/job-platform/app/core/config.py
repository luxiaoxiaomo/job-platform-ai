"""
应用配置管理
从环境变量读取配置
"""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    # 基础配置
    PROJECT_NAME: str = "空岗信息发布对接平台"
    ENV: str = "dev"  # dev/test/prod
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://dev:dev123@localhost:5432/jobplatform_dev"
    TEST_DATABASE_URL: str = "postgresql+asyncpg://dev:dev123@localhost:5432/jobplatform_test"
    DATABASE_ECHO: bool = False

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI服务配置
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    QWEN_API_KEY: str = ""  # 通义千问（备用）

    # JWT配置
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 120  # 2小时

    # 手机号哈希密钥（独立于JWT）
    PHONE_HASH_SECRET: str = "your-phone-hash-secret-change-in-production"

    # 字段加密配置
    ENCRYPTION_KEY: str = ""  # 32字节Fernet密钥

    # CORS配置
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]

    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = str(Path(__file__).resolve().parents[2] / "uploads")

    # OCR configuration
    OCR_PROVIDER: str = "mock"  # mock/rapidocr
    OCR_CONFIDENCE_THRESHOLD: float = 0.5
    OCR_PDF_MAX_PAGES: int = 3
    OCR_PDF_RENDER_SCALE: float = 2.0

    # WeChat notification preparation
    # dry_run keeps local behavior testable without real credentials.
    # live calls the WeChat service account template-message API.
    # disabled closes due push tasks without attempting external delivery.
    WECHAT_PUSH_MODE: str = "dry_run"  # disabled/dry_run/live
    WECHAT_API_BASE_URL: str = "https://api.weixin.qq.com"
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""
    WECHAT_TEMPLATE_ACTION_BASE_URL: str = ""
    WECHAT_TEMPLATE_DEFAULT: str = ""
    WECHAT_TEMPLATE_JOB_REVIEW: str = ""
    WECHAT_TEMPLATE_MESSAGE: str = ""
    WECHAT_TEMPLATE_APPLICATION: str = ""
    WECHAT_TEMPLATE_APPLICATION_STATUS: str = ""
    WECHAT_TEMPLATE_MATCH: str = ""

    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # 配置文件
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# 全局配置实例
def validate_production_settings(value: Settings) -> None:
    """Fail fast when production configuration is unsafe."""
    if value.ENV != "prod":
        return

    if value.DEBUG:
        raise ValueError("生产环境必须关闭DEBUG")

    secret_fields = {
        "SECRET_KEY": value.SECRET_KEY,
        "JWT_SECRET_KEY": value.JWT_SECRET_KEY,
        "PHONE_HASH_SECRET": value.PHONE_HASH_SECRET,
    }
    for field_name, secret in secret_fields.items():
        if len(secret.strip()) < 32 or "change-in-production" in secret:
            raise ValueError(f"生产环境必须配置安全的{field_name}")

    if not value.ENCRYPTION_KEY:
        raise ValueError("生产环境必须配置ENCRYPTION_KEY")

    database_url = value.DATABASE_URL.lower()
    if not database_url.startswith(("postgresql://", "postgresql+asyncpg://")):
        raise ValueError("生产环境数据库必须使用PostgreSQL")
    if "dev:dev123" in database_url or "localhost" in database_url or "/jobplatform_dev" in database_url:
        raise ValueError("生产环境不能使用默认数据库配置")

    if not value.ALLOWED_ORIGINS:
        raise ValueError("生产环境必须配置ALLOWED_ORIGINS")
    for origin in value.ALLOWED_ORIGINS:
        normalized = origin.strip().lower()
        if normalized == "*" or "localhost" in normalized or "127.0.0.1" in normalized:
            raise ValueError("生产环境ALLOWED_ORIGINS不能包含通配符或本地地址")
        if not normalized.startswith("https://"):
            raise ValueError("生产环境ALLOWED_ORIGINS必须使用HTTPS")


settings = Settings()
validate_production_settings(settings)
