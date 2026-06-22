"""
Job application API tests.
"""
from httpx import AsyncClient

from tests.test_api.test_company_certifications import register_and_get_token
from tests.test_api.test_jobs import approve_current_recruiter_certification, job_payload
from tests.test_api.test_matches import create_confirmed_resume_profile


async def create_active_job(
    client: AsyncClient,
    db_session,
    recruiter_data: dict,
) -> tuple[str, int]:
    recruiter_token = await register_and_get_token(client, recruiter_data)
    admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)
    create_response = await client.post(
        "/api/v1/jobs/me",
        json=job_payload(),
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    job_id = create_response.json()["id"]
    await client.post(
        f"/api/v1/jobs/admin/{job_id}/review",
        json={"action": "approve"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return recruiter_token, job_id


async def create_active_job_with_admin(
    client: AsyncClient,
    db_session,
    recruiter_data: dict,
) -> tuple[str, str, int]:
    recruiter_token = await register_and_get_token(client, recruiter_data)
    admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)
    create_response = await client.post(
        "/api/v1/jobs/me",
        json=job_payload(),
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    job_id = create_response.json()["id"]
    await client.post(
        f"/api/v1/jobs/admin/{job_id}/review",
        json={"action": "approve"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return recruiter_token, admin_token, job_id


async def upload_resume(client: AsyncClient, seeker_token: str) -> dict:
    response = await client.post(
        "/api/v1/resumes/me/upload",
        files={"file": ("resume.pdf", b"fake resume content", "application/pdf")},
        headers={"Authorization": f"Bearer {seeker_token}"},
    )
    assert response.status_code == 200
    return response.json()["resume"]


class TestApplications:
    async def test_seeker_can_generate_cover_letter_suggestion(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)
        create_job_response = await client.post(
            "/api/v1/jobs/me",
            json={
                **job_payload(),
                "title": "PeopleSoft 技术顾问",
                "tags": ["PeopleSoft", "SQL"],
                "requirement": "熟悉 PeopleSoft HCM 和 SQL。",
            },
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        job_id = create_job_response.json()["id"]
        await client.post(
            f"/api/v1/jobs/admin/{job_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        seeker_token = await register_and_get_token(client, test_user_data)
        await create_confirmed_resume_profile(client, seeker_token)

        response = await client.post(
            "/api/v1/applications/cover-letter/suggest",
            json={"job_id": job_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["source"] == "rule_fallback"
        assert data["fallback_used"] is True
        assert "PeopleSoft" in data["cover_message"]
        assert len(data["cover_message"]) <= 1000

    async def test_seeker_can_apply_to_active_job(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, job_id = await create_active_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)
        resume = await upload_resume(client, seeker_token)

        response = await client.post(
            "/api/v1/applications",
            json={
                "job_id": job_id,
                "resume_snapshot": "Backend engineer resume snapshot",
                "cover_message": "I am interested in this role.",
            },
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "submitted"
        assert data["cover_message"] == "I am interested in this role."
        assert data["resume_id"] == resume["id"]
        assert data["resume_file_url"] == resume["file_url"]
        assert data["resume_snapshot"] == resume["parsed_snapshot"]

        my_response = await client.get(
            "/api/v1/applications/me",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert my_response.status_code == 200
        assert my_response.json()["total"] == 1

        recruiter_response = await client.get(
            "/api/v1/applications/recruiter",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_response.status_code == 200
        assert recruiter_response.json()["total"] == 1

    async def test_seeker_cannot_apply_to_pending_job(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        await approve_current_recruiter_certification(client, db_session, recruiter_token)
        create_response = await client.post(
            "/api/v1/jobs/me",
            json=job_payload(),
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        seeker_token = await register_and_get_token(client, test_user_data)

        response = await client.post(
            "/api/v1/applications",
            json={"job_id": create_response.json()["id"]},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 400
        assert "active" in response.json()["detail"].lower()

    async def test_seeker_cannot_apply_without_resume(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        _, job_id = await create_active_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)

        response = await client.post(
            "/api/v1/applications",
            json={"job_id": job_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 400
        assert "resume" in response.json()["detail"].lower()

    async def test_seeker_cannot_apply_twice(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        _, job_id = await create_active_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)
        await upload_resume(client, seeker_token)

        first = await client.post(
            "/api/v1/applications",
            json={"job_id": job_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        second = await client.post(
            "/api/v1/applications",
            json={"job_id": job_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert first.status_code == 201
        assert second.status_code == 409

    async def test_recruiter_can_update_own_application_status(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, job_id = await create_active_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)
        await upload_resume(client, seeker_token)
        apply_response = await client.post(
            "/api/v1/applications",
            json={"job_id": job_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        application_id = apply_response.json()["id"]

        response = await client.post(
            f"/api/v1/applications/{application_id}/status",
            json={"status": "interview_invited"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "interview_invited"
        assert data["viewed_at"] is not None

        detail_response = await client.get(
            f"/api/v1/applications/recruiter/{application_id}",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["id"] == application_id
        assert [item["to_status"] for item in detail["timeline"]] == ["submitted", "interview_invited"]

    async def test_recruiter_application_stats_summary_counts_statuses(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, job_id = await create_active_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)
        await upload_resume(client, seeker_token)
        apply_response = await client.post(
            "/api/v1/applications",
            json={"job_id": job_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        application_id = apply_response.json()["id"]

        initial_response = await client.get(
            "/api/v1/applications/recruiter/stats/summary",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert initial_response.status_code == 200
        assert initial_response.json() == {
            "submitted_count": 1,
            "viewed_count": 0,
            "interview_invited_count": 0,
            "rejected_count": 0,
            "hired_count": 0,
            "total_count": 1,
        }

        await client.post(
            f"/api/v1/applications/{application_id}/status",
            json={"status": "interview_invited"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        updated_response = await client.get(
            "/api/v1/applications/recruiter/stats/summary",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert updated_response.status_code == 200
        assert updated_response.json() == {
            "submitted_count": 0,
            "viewed_count": 0,
            "interview_invited_count": 1,
            "rejected_count": 0,
            "hired_count": 0,
            "total_count": 1,
        }

        seeker_response = await client.get(
            "/api/v1/applications/recruiter/stats/summary",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert seeker_response.status_code == 403

    async def test_admin_application_stats_summary_counts_platform_statuses(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, admin_token, job_id = await create_active_job_with_admin(
            client,
            db_session,
            test_recruiter_data,
        )
        seeker_token = await register_and_get_token(client, test_user_data)
        await upload_resume(client, seeker_token)
        apply_response = await client.post(
            "/api/v1/applications",
            json={"job_id": job_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        application_id = apply_response.json()["id"]
        await client.post(
            f"/api/v1/applications/{application_id}/status",
            json={"status": "hired"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        response = await client.get(
            "/api/v1/applications/admin/stats/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json() == {
            "submitted_count": 0,
            "viewed_count": 0,
            "interview_invited_count": 0,
            "rejected_count": 0,
            "hired_count": 1,
            "total_count": 1,
        }

        recruiter_response = await client.get(
            "/api/v1/applications/admin/stats/summary",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_response.status_code == 403

    async def test_recruiter_can_download_own_application_resume(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, job_id = await create_active_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)
        await upload_resume(client, seeker_token)
        apply_response = await client.post(
            "/api/v1/applications",
            json={"job_id": job_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        application_id = apply_response.json()["id"]

        response = await client.get(
            f"/api/v1/applications/recruiter/{application_id}/resume-file",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert response.status_code == 200
        assert response.content == b"fake resume content"

    async def test_recruiter_cannot_update_other_recruiters_application(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        _, job_id = await create_active_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)
        await upload_resume(client, seeker_token)
        apply_response = await client.post(
            "/api/v1/applications",
            json={"job_id": job_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        application_id = apply_response.json()["id"]

        other_recruiter = {
            "phone": "13900139009",
            "password": "Recruiter123",
            "display_name": "Other recruiter",
            "role": "recruiter",
        }
        other_token = await register_and_get_token(client, other_recruiter)

        response = await client.post(
            f"/api/v1/applications/{application_id}/status",
            json={"status": "viewed"},
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert response.status_code == 404

        detail_response = await client.get(
            f"/api/v1/applications/recruiter/{application_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        download_response = await client.get(
            f"/api/v1/applications/recruiter/{application_id}/resume-file",
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert detail_response.status_code == 404
        assert download_response.status_code == 404

    async def test_rejected_status_requires_reason(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, job_id = await create_active_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)
        await upload_resume(client, seeker_token)
        apply_response = await client.post(
            "/api/v1/applications",
            json={"job_id": job_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        application_id = apply_response.json()["id"]

        response = await client.post(
            f"/api/v1/applications/{application_id}/status",
            json={"status": "rejected"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert response.status_code == 400
