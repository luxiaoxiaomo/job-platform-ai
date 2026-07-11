import pytest

from app.modules.user.models import User
from app.utils.encryption import encryptor
from app.utils.phone_hash import hash_phone
from scripts.seed_rp401_demo import get_or_create_user


@pytest.mark.asyncio
async def test_existing_demo_user_phone_is_reencrypted_with_active_key(db_session):
    phone = "13699990001"
    user = User(
        phone_hash=hash_phone(phone),
        phone_encrypted=encryptor.encrypt("13699990002"),
        password_hash="stale-password-hash",
        display_name="旧演示账号",
        role="recruiter",
        status="active",
    )
    db_session.add(user)
    await db_session.commit()

    updated = await get_or_create_user(
        db_session,
        phone=phone,
        role="recruiter",
        display_name="演示招聘者",
        password="Recruiter123",
    )

    assert encryptor.decrypt(updated.phone_encrypted) == phone
