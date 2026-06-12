"""
Job posting API tests.
"""
from httpx import AsyncClient

from tests.test_api.test_company_certifications import (
    certification_payload,
    create_admin_token,
    register_and_get_token,
)


def job_payload() -> dict:
    return {
        "title": "前端开发工程师",
        "city": "深圳",
        "salary_min": 15,
        "salary_max": 25,
        "experience": "3-5年",
        "education": "本科",
        "description": "负责招聘平台前端页面开发、组件维护和性能优化。",
        "requirement": "熟悉 React 和 TypeScript，有真实项目交付经验。",
        "benefits": "五险一金、双休",
        "tags": ["React", "TypeScript"],
    }


async def approve_current_recruiter_certification(client: AsyncClient, db_session, recruiter_token: str) -> str:
    await client.post(
        "/api/v1/company-certifications/me",
        json=certification_payload(),
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    admin_token = await create_admin_token(client, db_session)
    response = await client.get(
        "/api/v1/company-certifications/admin",
        params={"status": "pending"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    certification_id = response.json()["items"][0]["id"]
    await client.post(
        f"/api/v1/company-certifications/admin/{certification_id}/review",
        json={"action": "approve"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return admin_token


class TestJobs:
    async def test_recruiter_must_be_certified_before_create_job(
        self,
        client: AsyncClient,
        test_recruiter_data,
    ):
        token = await register_and_get_token(client, test_recruiter_data)

        response = await client.post(
            "/api/v1/jobs/me",
            json=job_payload(),
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403
        assert "certification" in response.json()["detail"].lower()

    async def test_certified_recruiter_create_job_defaults_to_pending(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
    ):
        token = await register_and_get_token(client, test_recruiter_data)
        await approve_current_recruiter_certification(client, db_session, token)

        response = await client.post(
            "/api/v1/jobs/me",
            json=job_payload(),
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["title"] == "前端开发工程师"
        assert data["published_at"] is None

        list_response = await client.get(
            "/api/v1/jobs/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_response.status_code == 200
        assert list_response.json()["total"] == 1

    async def test_admin_approve_job_makes_it_public(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)
        create_response = await client.post(
            "/api/v1/jobs/me",
            json=job_payload(),
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        job_id = create_response.json()["id"]

        review_response = await client.post(
            f"/api/v1/jobs/admin/{job_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert review_response.status_code == 200
        assert review_response.json()["status"] == "active"
        assert review_response.json()["published_at"] is not None

        seeker_token = await register_and_get_token(client, test_user_data)
        public_response = await client.get(
            "/api/v1/jobs/public",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert public_response.status_code == 200
        data = public_response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == job_id

    async def test_recruiter_can_parse_jd_text_file(
        self,
        client: AsyncClient,
        test_recruiter_data,
    ):
        token = await register_and_get_token(client, test_recruiter_data)
        jd_text = """
岗位名称：前端开发工程师
工作城市：上海
薪资：15-25K
工作经验：1-3年
学历：本科
岗位职责：
负责招聘平台前端页面开发、接口联调和性能优化。
任职要求：
熟悉 React 和 JavaScript，有真实项目交付经验。
福利待遇：
五险一金、带薪年假。
"""

        response = await client.post(
            "/api/v1/jobs/parse-jd",
            files={"file": ("frontend-jd.txt", jd_text.encode("utf-8"), "text/plain")},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "前端开发工程师"
        assert data["city"] == "上海"
        assert data["salary_min"] == 15
        assert data["salary_max"] == 25
        assert "招聘平台前端页面开发" in data["description"]
        assert "React" in data["requirement"]
        assert data["raw_text"]

    async def test_recruiter_can_parse_pasted_jd_text(
        self,
        client: AsyncClient,
        test_recruiter_data,
    ):
        token = await register_and_get_token(client, test_recruiter_data)
        jd_text = """
岗位名称：后端开发工程师
工作城市：杭州
薪资：20-35K
岗位职责：
负责招聘平台后端接口开发、数据建模和服务稳定性优化。
任职要求：
熟悉 Python 和 FastAPI，理解数据库设计和接口鉴权。
"""

        response = await client.post(
            "/api/v1/jobs/parse-jd-text",
            json={"text": jd_text},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "后端开发工程师"
        assert data["city"] == "杭州"
        assert data["salary_min"] == 20
        assert data["salary_max"] == 35
        assert "后端接口开发" in data["description"]
        assert "FastAPI" in data["requirement"]

    async def test_seeker_cannot_parse_jd_file(
        self,
        client: AsyncClient,
        test_user_data,
    ):
        token = await register_and_get_token(client, test_user_data)

        response = await client.post(
            "/api/v1/jobs/parse-jd",
            files={"file": ("jd.txt", b"job description", "text/plain")},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    async def test_recruiter_can_get_rule_based_salary_suggestion(
        self,
        client: AsyncClient,
        test_recruiter_data,
    ):
        token = await register_and_get_token(client, test_recruiter_data)

        backend_response = await client.post(
            "/api/v1/jobs/salary-suggestion",
            json={
                "title": "后端开发工程师",
                "city": "杭州",
                "experience": "3-5年",
                "education": "本科",
                "tags": ["后端开发", "Python", "FastAPI"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        frontend_response = await client.post(
            "/api/v1/jobs/salary-suggestion",
            json={
                "title": "前端开发工程师",
                "city": "深圳",
                "experience": "1-3年",
                "education": "本科",
                "tags": ["前端开发", "React", "TypeScript"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert backend_response.status_code == 200
        assert frontend_response.status_code == 200
        backend = backend_response.json()
        frontend = frontend_response.json()
        assert backend["salary_min"] >= 20
        assert backend["salary_max"] > backend["salary_min"]
        assert "后端开发" in backend["factors"]
        assert "前端开发" in frontend["factors"]
        assert backend["basis"] != frontend["basis"]
