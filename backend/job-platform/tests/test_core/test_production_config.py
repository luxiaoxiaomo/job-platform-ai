"""Production configuration validation tests."""

import pytest

from app.core.config import Settings, validate_production_settings


def production_settings(**overrides) -> Settings:
    values = {
        "ENV": "prod",
        "DEBUG": False,
        "SECRET_KEY": "s" * 32,
        "JWT_SECRET_KEY": "j" * 32,
        "PHONE_HASH_SECRET": "p" * 32,
        "ENCRYPTION_KEY": "DjMvO5B0ZUlwiBNx2THNP_eW3usmxPaByHxwQJOZEeE=",
        "DATABASE_URL": "postgresql+asyncpg://app:secret@db.internal:5432/jobplatform",
        "ALLOWED_ORIGINS": ["https://jobs.example.com"],
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"DEBUG": True}, "DEBUG"),
        ({"SECRET_KEY": "short"}, "SECRET_KEY"),
        ({"ALLOWED_ORIGINS": ["*"]}, "ALLOWED_ORIGINS"),
        ({"ALLOWED_ORIGINS": ["http://localhost:5174"]}, "ALLOWED_ORIGINS"),
        ({"DATABASE_URL": "sqlite:///prod.db"}, "PostgreSQL"),
    ],
)
def test_production_settings_reject_unsafe_values(override, message):
    with pytest.raises(ValueError, match=message):
        validate_production_settings(production_settings(**override))


def test_production_settings_accept_hardened_values():
    validate_production_settings(production_settings())
