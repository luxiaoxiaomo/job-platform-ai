"""Search API tests."""
from httpx import AsyncClient

from tests.test_api.test_company_certifications import register_and_get_token
from tests.test_api.test_jobs import approve_current_recruiter_certification, job_payload
from tests.test_api.test_matches import create_confirmed_resume_profile


class TestSearch:
    async def test_seeker_can_search_active_jobs(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)
        create_response = await client.post(
            "/api/v1/jobs/me",
            json={
                **job_payload(),
                "title": "React 前端开发工程师",
                "description": "负责 React 招聘平台前端页面和组件开发。",
                "requirement": "熟悉 React、TypeScript 和组件化工程。",
                "tags": ["React", "TypeScript"],
            },
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        job_id = create_response.json()["id"]
        await client.post(
            f"/api/v1/jobs/admin/{job_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        seeker_token = await register_and_get_token(client, test_user_data)

        response = await client.get(
            "/api/v1/search/jobs",
            params={"q": "React 前端"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "keyword_semantic_fallback"
        assert data["total"] == 1
        assert data["items"][0]["id"] == job_id
        assert data["items"][0]["score"] > 0
        assert "react" in data["items"][0]["reason"].lower()

    async def test_seeker_can_filter_job_search_by_tag_id(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        tag_response = await client.post(
            "/api/v1/base-data/tags",
            json={"name": "React", "category": "技能"},
            headers=admin_headers,
        )
        other_tag_response = await client.post(
            "/api/v1/base-data/tags",
            json={"name": "Python", "category": "技能"},
            headers=admin_headers,
        )
        tag = tag_response.json()
        other_tag = other_tag_response.json()
        create_response = await client.post(
            "/api/v1/jobs/me",
            json={**job_payload(), "title": "React 前端开发工程师", "tag_ids": [tag["id"]]},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        job_id = create_response.json()["id"]
        await client.post(
            f"/api/v1/jobs/admin/{job_id}/review",
            json={"action": "approve"},
            headers=admin_headers,
        )
        seeker_token = await register_and_get_token(client, test_user_data)

        matched = await client.get(
            "/api/v1/search/jobs",
            params={"q": "前端", "tag_id": tag["id"]},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        missed = await client.get(
            "/api/v1/search/jobs",
            params={"q": "前端", "tag_id": other_tag["id"]},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert matched.status_code == 200
        assert matched.json()["total"] == 1
        assert matched.json()["items"][0]["id"] == job_id
        assert matched.json()["items"][0]["tag_refs"][0]["id"] == tag["id"]
        assert missed.status_code == 200
        assert missed.json()["total"] == 0

    async def test_recruiter_can_search_confirmed_resumes(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        seeker_token = await register_and_get_token(client, test_user_data)
        await create_confirmed_resume_profile(client, seeker_token)
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        await approve_current_recruiter_certification(client, db_session, recruiter_token)

        response = await client.get(
            "/api/v1/search/resumes",
            params={"q": "PeopleSoft SQL"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "keyword_semantic_fallback"
        assert data["total"] == 1
        item = data["items"][0]
        assert item["seeker_id"]
        assert item["structured_profile_id"]
        assert item["score"] > 0
        assert "PeopleSoft" in item["skills"]

    async def test_recruiter_can_filter_resume_search_by_tag_id(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)
        tag_response = await client.post(
            "/api/v1/base-data/tags",
            json={"name": "PeopleSoft", "category": "技能"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        other_tag_response = await client.post(
            "/api/v1/base-data/tags",
            json={"name": "React", "category": "技能"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        tag = tag_response.json()
        other_tag = other_tag_response.json()
        seeker_token = await register_and_get_token(client, test_user_data)
        await create_confirmed_resume_profile(client, seeker_token)
        profile_response = await client.put(
            "/api/v1/seeker-profiles/me",
            json={
                "real_name": "曾振宇",
                "gender": "男",
                "education": "本科",
                "experience_years": 4,
                "target_position": "PeopleSoft 技术顾问",
                "tag_ids": [tag["id"]],
            },
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert profile_response.status_code == 200
        matched = await client.get(
            "/api/v1/search/resumes",
            params={"q": "PeopleSoft SQL", "tag_id": tag["id"]},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        missed = await client.get(
            "/api/v1/search/resumes",
            params={"q": "PeopleSoft SQL", "tag_id": other_tag["id"]},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert matched.status_code == 200
        assert matched.json()["total"] == 1
        assert matched.json()["items"][0]["tag_refs"][0]["id"] == tag["id"]
        assert missed.status_code == 200
        assert missed.json()["total"] == 0

    async def test_recruiter_can_filter_resume_search_by_structured_profile_tag_id(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)
        tag_response = await client.post(
            "/api/v1/base-data/tags",
            json={"name": "PeopleSoft", "category": "技能"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        tag = tag_response.json()
        seeker_token = await register_and_get_token(client, test_user_data)
        profile = await create_confirmed_resume_profile(
            client,
            seeker_token,
            tag_ids=[tag["id"]],
            return_profile=True,
        )

        response = await client.get(
            "/api/v1/search/resumes",
            params={"q": "PeopleSoft SQL", "tag_id": tag["id"]},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["structured_profile_id"] == profile["id"]
        assert data["items"][0]["tag_refs"][0]["id"] == tag["id"]

    async def test_search_role_guards(
        self,
        client: AsyncClient,
        test_user_data,
        test_recruiter_data,
    ):
        seeker_token = await register_and_get_token(client, test_user_data)
        recruiter_token = await register_and_get_token(client, test_recruiter_data)

        jobs_response = await client.get(
            "/api/v1/search/jobs",
            params={"q": "React"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        resumes_response = await client.get(
            "/api/v1/search/resumes",
            params={"q": "React"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert jobs_response.status_code == 403
        assert resumes_response.status_code == 403
