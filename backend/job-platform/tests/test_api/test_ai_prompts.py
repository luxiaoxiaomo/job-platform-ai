"""
AI prompt configuration API tests.
"""
from httpx import AsyncClient

from tests.test_api.test_company_certifications import create_admin_token, register_and_get_token


def prompt_payload() -> dict:
    return {
        "scenario_key": "job_content_review",
        "name": "岗位内容预审 v2",
        "system_prompt": "你是招聘平台岗位内容审核助手，只输出 JSON。",
        "user_prompt_template": "请审核岗位：$title\n职责：$description\n要求：$requirement",
        "output_schema": '{"level":"pass|warning|block","summary":"string","findings":[]}',
    }


def pre_review_payload(**overrides) -> dict:
    payload = {
        "title": "后端开发工程师",
        "city": "杭州",
        "salary_min": 20,
        "salary_max": 35,
        "experience": "3-5年",
        "education": "本科",
        "description": "负责招聘平台后端核心接口开发、数据建模、审核流状态流转和服务稳定性优化。",
        "requirement": "熟悉 Python 和 FastAPI，理解数据库设计、接口鉴权、权限控制和线上问题定位。",
        "benefits": "五险一金",
        "tags": ["后端开发", "Python", "FastAPI"],
    }
    payload.update(overrides)
    return payload


class TestAiPrompts:
    async def test_admin_can_get_default_active_prompt(self, client: AsyncClient, db_session):
        admin_token = await create_admin_token(client, db_session)

        response = await client.get(
            "/api/v1/ai-prompts/active",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["scenario_key"] == "job_content_review"
        assert data["is_active"] is True
        assert "岗位内容审核" in data["system_prompt"]

    async def test_admin_can_create_and_publish_prompt(self, client: AsyncClient, db_session):
        admin_token = await create_admin_token(client, db_session)

        create_response = await client.post(
            "/api/v1/ai-prompts",
            json=prompt_payload(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert create_response.status_code == 201
        created = create_response.json()
        assert created["version"] == 1
        assert created["is_active"] is False

        publish_response = await client.post(
            f"/api/v1/ai-prompts/{created['id']}/publish",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert publish_response.status_code == 200
        assert publish_response.json()["is_active"] is True

    async def test_recruiter_can_run_job_pre_review(self, client: AsyncClient, test_recruiter_data):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)

        response = await client.post(
            "/api/v1/ai-prompts/job-content-review",
            json=pre_review_payload(),
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "pass"
        assert data["prompt_source"] == "default_prompt"

    async def test_job_pre_review_blocks_discrimination(self, client: AsyncClient, test_recruiter_data):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)

        response = await client.post(
            "/api/v1/ai-prompts/job-content-review",
            json=pre_review_payload(requirement="仅限男性，熟悉 Python 和 FastAPI。"),
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "block"
        assert data["findings"][0]["category"] == "歧视性用语"
