import pytest


pytestmark = pytest.mark.asyncio


async def _register_and_login(client, payload):
    register_payload = {
        **payload,
        "verification_code": "123456",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    response = await client.post(
        "/api/v1/auth/login",
        json={"phone": payload["phone"], "password": payload["password"]},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def test_seeker_can_save_and_read_profile(client, test_user_data):
    token = await _register_and_login(client, test_user_data)
    headers = {"Authorization": f"Bearer {token}"}

    initial = await client.get("/api/v1/seeker-profiles/me", headers=headers)
    assert initial.status_code == 200
    assert initial.json()["is_complete"] is False

    payload = {
        "real_name": "雷神",
        "gender": "男",
        "education": "本科",
        "experience_years": 5,
        "target_position": "后端开发工程师",
        "expected_salary": "20K-30K",
        "city": "深圳",
        "name_public": True,
        "phone_public": False,
        "education_public": True,
        "experience_public": True,
    }
    saved = await client.put("/api/v1/seeker-profiles/me", json=payload, headers=headers)
    assert saved.status_code == 200
    data = saved.json()
    assert data["real_name"] == "雷神"
    assert data["is_complete"] is True
    assert data["phone_public"] is False

    fetched = await client.get("/api/v1/seeker-profiles/me", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["target_position"] == "后端开发工程师"


async def test_recruiter_cannot_use_seeker_profile(client, test_recruiter_data):
    token = await _register_and_login(client, test_recruiter_data)

    response = await client.get(
        "/api/v1/seeker-profiles/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
