"""
Job application API tests.
"""
from httpx import AsyncClient

from tests.test_api.test_company_certifications import register_and_get_token
from tests.test_api.test_jobs import approve_current_recruiter_certification, job_payload


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


class TestApplications:
    async def test_seeker_can_apply_to_active_job(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, job_id = await create_active_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)

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

    async def test_seeker_cannot_apply_twice(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        _, job_id = await create_active_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)

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

    async def test_recruiter_cannot_update_other_recruiters_application(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        _, job_id = await create_active_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)
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

    async def test_rejected_status_requires_reason(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, job_id = await create_active_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)
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
