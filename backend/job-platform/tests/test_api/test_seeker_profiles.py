import pytest

from tests.test_api.test_company_certifications import create_admin_token


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
        "email": "candidate@example.com",
        "wechat": "candidate_wx",
        "email_public": True,
        "wechat_public": True,
        "education_public": True,
        "experience_public": True,
    }
    saved = await client.put("/api/v1/seeker-profiles/me", json=payload, headers=headers)
    assert saved.status_code == 200
    data = saved.json()
    assert data["real_name"] == "雷神"
    assert data["is_complete"] is True
    assert data["phone_public"] is False
    assert data["email"] == "candidate@example.com"
    assert data["wechat"] == "candidate_wx"
    assert data["email_public"] is True
    assert data["wechat_public"] is True

    fetched = await client.get("/api/v1/seeker-profiles/me", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["target_position"] == "后端开发工程师"


async def test_seeker_can_link_profile_to_standard_position(client, db_session, test_user_data):
    admin_token = await create_admin_token(client, db_session)
    create_position = await client.post(
        "/api/v1/base-data/standard-positions",
        json={"name": "后端开发工程师", "category": "技术研发", "aliases": ["后端工程师"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_position.status_code == 201
    position = create_position.json()

    token = await _register_and_login(client, test_user_data)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "real_name": "李然",
        "gender": "男",
        "education": "本科",
        "experience_years": 5,
        "target_position": "后端开发工程师",
        "standard_position_id": position["id"],
        "expected_salary": "20K-30K",
        "city": "深圳",
    }
    saved = await client.put("/api/v1/seeker-profiles/me", json=payload, headers=headers)

    assert saved.status_code == 200
    data = saved.json()
    assert data["standard_position_id"] == position["id"]
    assert data["standard_position_name"] == "后端开发工程师"


async def test_seeker_can_link_profile_to_tag_library_items(client, db_session, test_user_data):
    admin_token = await create_admin_token(client, db_session)
    create_tag = await client.post(
        "/api/v1/base-data/tags",
        json={"name": "Python", "category": "技能", "color": "#3776ab"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_tag.status_code == 201
    tag = create_tag.json()

    token = await _register_and_login(client, test_user_data)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "real_name": "李然",
        "gender": "男",
        "education": "本科",
        "experience_years": 5,
        "target_position": "后端开发工程师",
        "tag_ids": [tag["id"]],
        "expected_salary": "20K-30K",
        "city": "深圳",
    }
    saved = await client.put("/api/v1/seeker-profiles/me", json=payload, headers=headers)

    assert saved.status_code == 200
    data = saved.json()
    assert data["tag_refs"] == [
        {"id": tag["id"], "name": "Python", "category": "技能", "color": "#3776ab"}
    ]


async def test_seeker_cannot_link_profile_to_missing_tag_library_item(client, test_user_data):
    token = await _register_and_login(client, test_user_data)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "real_name": "李然",
        "gender": "男",
        "education": "本科",
        "experience_years": 5,
        "target_position": "后端开发工程师",
        "tag_ids": [999999],
    }
    saved = await client.put("/api/v1/seeker-profiles/me", json=payload, headers=headers)

    assert saved.status_code == 404
    assert saved.json()["detail"] == "Tag not found"


async def test_seeker_cannot_link_profile_to_missing_standard_position(client, test_user_data):
    token = await _register_and_login(client, test_user_data)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "real_name": "李然",
        "gender": "男",
        "education": "本科",
        "experience_years": 5,
        "target_position": "后端开发工程师",
        "standard_position_id": 999999,
    }
    saved = await client.put("/api/v1/seeker-profiles/me", json=payload, headers=headers)

    assert saved.status_code == 404
    assert saved.json()["detail"] == "Standard position not found"


async def test_recruiter_cannot_use_seeker_profile(client, test_recruiter_data):
    token = await _register_and_login(client, test_recruiter_data)

    response = await client.get(
        "/api/v1/seeker-profiles/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
