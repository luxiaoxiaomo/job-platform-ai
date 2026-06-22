"""
End-to-end API coverage for the minimum PRD business loop.
"""
from httpx import AsyncClient

from tests.test_api.test_applications import upload_resume
from tests.test_api.test_company_certifications import (
    register_and_get_token,
)
from tests.test_api.test_jobs import approve_current_recruiter_certification, job_payload


class TestMinimumBusinessLoop:
    async def test_recruiter_job_review_seeker_message_application_and_contact_exchange(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)

        create_job = await client.post(
            "/api/v1/jobs/me",
            json=job_payload(),
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert create_job.status_code == 201
        job_id = create_job.json()["id"]
        assert create_job.json()["status"] == "pending"

        admin_jobs = await client.get(
            "/api/v1/jobs/admin",
            params={"status": "pending"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_jobs.status_code == 200
        assert any(item["id"] == job_id for item in admin_jobs.json()["items"])

        approve_job = await client.post(
            f"/api/v1/jobs/admin/{job_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert approve_job.status_code == 200
        assert approve_job.json()["status"] == "active"

        public_jobs = await client.get("/api/v1/jobs/public")
        assert public_jobs.status_code == 200
        assert any(item["id"] == job_id for item in public_jobs.json()["items"])

        public_detail = await client.get(f"/api/v1/jobs/public/{job_id}")
        assert public_detail.status_code == 200
        assert public_detail.json()["id"] == job_id
        assert public_detail.json()["view_count"] == 1

        seeker_token = await register_and_get_token(client, test_user_data)

        open_conversation = await client.post(
            "/api/v1/messages/conversations/open",
            json={"job_id": job_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert open_conversation.status_code == 201
        conversation_id = open_conversation.json()["id"]
        assert open_conversation.json()["job_id"] == job_id

        recruiter_conversations = await client.get(
            "/api/v1/messages/conversations",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_conversations.status_code == 200
        assert recruiter_conversations.json()["total"] == 1
        assert recruiter_conversations.json()["items"][0]["id"] == conversation_id

        recruiter_jobs_after_message = await client.get(
            "/api/v1/jobs/me",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_jobs_after_message.status_code == 200
        assert recruiter_jobs_after_message.json()["items"][0]["conversation_count"] == 1

        recruiter_reply = await client.post(
            f"/api/v1/messages/conversations/{conversation_id}/messages",
            json={"content": "Thanks, please send your resume through the platform."},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_reply.status_code == 200
        assert recruiter_reply.json()["messages"][-1]["sender_role"] == "recruiter"

        resume = await upload_resume(client, seeker_token)
        application = await client.post(
            "/api/v1/applications",
            json={"job_id": job_id, "cover_message": "I would like to apply."},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert application.status_code == 201
        application_id = application.json()["id"]
        assert application.json()["resume_id"] == resume["id"]

        seeker_application_detail = await client.get(
            f"/api/v1/applications/me/{application_id}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert seeker_application_detail.status_code == 200
        assert seeker_application_detail.json()["timeline"][0]["to_status"] == "submitted"

        recruiter_applications = await client.get(
            "/api/v1/applications/recruiter",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_applications.status_code == 200
        assert any(item["id"] == application_id for item in recruiter_applications.json()["items"])

        recruiter_application_detail = await client.get(
            f"/api/v1/applications/recruiter/{application_id}",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_application_detail.status_code == 200
        assert recruiter_application_detail.json()["job_id"] == job_id

        update_application = await client.post(
            f"/api/v1/applications/{application_id}/status",
            json={"status": "viewed"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert update_application.status_code == 200
        assert update_application.json()["status"] == "viewed"

        recruiter_application_stats = await client.get(
            "/api/v1/applications/recruiter/stats/summary",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_application_stats.status_code == 200
        assert recruiter_application_stats.json() == {
            "submitted_count": 0,
            "viewed_count": 1,
            "interview_invited_count": 0,
            "rejected_count": 0,
            "hired_count": 0,
            "total_count": 1,
        }

        admin_application_stats = await client.get(
            "/api/v1/applications/admin/stats/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_application_stats.status_code == 200
        assert admin_application_stats.json() == {
            "submitted_count": 0,
            "viewed_count": 1,
            "interview_invited_count": 0,
            "rejected_count": 0,
            "hired_count": 0,
            "total_count": 1,
        }

        request_exchange = await client.post(
            "/api/v1/messages/contact-exchanges",
            json={"conversation_id": conversation_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert request_exchange.status_code == 201
        exchange_id = request_exchange.json()["id"]
        assert request_exchange.json()["status"] == "pending"

        accept_exchange = await client.post(
            f"/api/v1/messages/contact-exchanges/{exchange_id}/review",
            json={"action": "accept"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert accept_exchange.status_code == 200
        assert accept_exchange.json()["status"] == "accepted"
        assert {item["role"] for item in accept_exchange.json()["contacts"]} == {"seeker", "recruiter"}

        seeker_conversation_detail = await client.get(
            f"/api/v1/messages/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert seeker_conversation_detail.status_code == 200
        assert seeker_conversation_detail.json()["contact_exchange"]["status"] == "accepted"

        recruiter_conversation_detail = await client.get(
            f"/api/v1/messages/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_conversation_detail.status_code == 200
        assert recruiter_conversation_detail.json()["contact_exchange"]["status"] == "accepted"

        recruiter_stats = await client.get(
            "/api/v1/messages/contact-exchanges/stats/summary",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_stats.status_code == 200
        assert recruiter_stats.json() == {
            "accepted_count": 1,
            "pending_count": 0,
            "declined_count": 0,
            "total_count": 1,
        }

        admin_stats = await client.get(
            "/api/v1/messages/contact-exchanges/stats/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_stats.status_code == 200
        assert admin_stats.json() == {
            "accepted_count": 1,
            "pending_count": 0,
            "declined_count": 0,
            "total_count": 1,
        }

        recruiter_loop_stats = await client.get(
            "/api/v1/applications/recruiter/stats/business-loop",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_loop_stats.status_code == 200
        assert recruiter_loop_stats.json() == {
            "job_count": 1,
            "view_count": 1,
            "conversation_count": 1,
            "application_count": 1,
            "submitted_count": 0,
            "processed_count": 1,
            "viewed_count": 1,
            "interview_invited_count": 0,
            "rejected_count": 0,
            "hired_count": 0,
            "contact_exchange_count": 1,
            "successful_connection_count": 1,
            "pending_exchange_count": 0,
            "declined_exchange_count": 0,
            "view_to_conversation_rate": 100.0,
            "conversation_to_application_rate": 100.0,
            "application_process_rate": 100.0,
            "application_to_connection_rate": 100.0,
            "successful_connection_definition": "contact_exchange.status = accepted",
        }

        admin_loop_stats = await client.get(
            "/api/v1/applications/admin/stats/business-loop",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_loop_stats.status_code == 200
        assert admin_loop_stats.json() == recruiter_loop_stats.json()

        recruiter_deep_dive = await client.get(
            "/api/v1/applications/recruiter/stats/deep-dive",
            params={"days": 7, "limit": 3},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_deep_dive.status_code == 200
        deep_dive = recruiter_deep_dive.json()
        assert deep_dive["summary"] == recruiter_loop_stats.json()
        assert deep_dive["trend_days"] == 7
        assert len(deep_dive["trend"]) == 7
        assert sum(item["application_count"] for item in deep_dive["trend"]) == 1
        assert sum(item["successful_connection_count"] for item in deep_dive["trend"]) == 1
        assert deep_dive["application_status_distribution"]["viewed"] == 1
        assert deep_dive["top_jobs"][0]["job_id"] == job_id
        assert deep_dive["top_jobs"][0]["view_count"] == 1
        assert deep_dive["top_jobs"][0]["application_count"] == 1
        assert deep_dive["top_jobs"][0]["successful_connection_count"] == 1
        assert deep_dive["top_jobs"][0]["application_rate"] == 100.0
        assert deep_dive["top_jobs"][0]["connection_rate"] == 100.0

        admin_deep_dive = await client.get(
            "/api/v1/applications/admin/stats/deep-dive",
            params={"days": 7, "limit": 3},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_deep_dive.status_code == 200
        assert admin_deep_dive.json()["summary"] == recruiter_loop_stats.json()

        admin_operations_stats = await client.get(
            "/api/v1/applications/admin/stats/operations",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_operations_stats.status_code == 200
        operations = admin_operations_stats.json()
        assert operations["today_new_user_count"] >= 2
        assert operations["today_new_job_count"] == 1
        assert operations["today_new_application_count"] == 1
        assert operations["active_job_count"] == 1
        assert operations["pending_job_review_count"] == 0
        assert operations["pending_certification_count"] == 0
        assert operations["approved_certification_count"] == 1
        assert operations["certification_total_count"] == 1
        assert operations["certification_approval_rate"] == 100.0
        assert operations["application_process_rate"] == 100.0
