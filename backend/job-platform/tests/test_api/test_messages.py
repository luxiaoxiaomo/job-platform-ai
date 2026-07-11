"""
Conversation and contact exchange API tests.
"""
from httpx import AsyncClient

from tests.test_api.test_applications import create_active_job, upload_resume
from tests.test_api.test_company_certifications import register_and_get_token
from tests.test_api.test_jobs import (
    approve_current_recruiter_certification_with_payload,
    job_payload,
)


async def create_conversation(client: AsyncClient, recruiter_data: dict, seeker_data: dict, db_session):
    recruiter_token, job_id = await create_active_job(client, db_session, recruiter_data)
    seeker_token = await register_and_get_token(client, seeker_data)
    response = await client.post(
        "/api/v1/messages/messages",
        json={"job_id": job_id, "content": "您好，我对这个岗位很感兴趣。"},
        headers={"Authorization": f"Bearer {seeker_token}"},
    )
    assert response.status_code == 201
    return recruiter_token, seeker_token, job_id, response.json()


class TestMessages:
    async def test_recruiter_can_get_reply_suggestions(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, _, _, detail = await create_conversation(
            client,
            test_recruiter_data,
            test_user_data,
            db_session,
        )

        response = await client.post(
            f"/api/v1/messages/conversations/{detail['id']}/reply-suggestions",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == detail["id"]
        assert data["scenario_key"] == "message_reply_suggestion"
        assert data["source"] == "template_fallback"
        assert len(data["suggestions"]) == 3
        assert all(item["text"].strip() for item in data["suggestions"])
        assert all(item["source"] == data["source"] for item in data["suggestions"])

    async def test_reply_suggestions_require_conversation_member(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        _, _, _, detail = await create_conversation(
            client,
            test_recruiter_data,
            test_user_data,
            db_session,
        )
        other_user = {
            **test_user_data,
            "phone": "13800138111",
            "display_name": "Other Seeker",
        }
        other_token = await register_and_get_token(client, other_user)

        response = await client.post(
            f"/api/v1/messages/conversations/{detail['id']}/reply-suggestions",
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert response.status_code == 404

    async def test_seeker_can_open_conversation_without_sending_message(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, job_id = await create_active_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)

        response = await client.post(
            "/api/v1/messages/conversations/open",
            json={"job_id": job_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["job_id"] == job_id
        assert data["messages"] == []

        recruiter_list = await client.get(
            "/api/v1/messages/conversations",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_list.status_code == 200
        assert recruiter_list.json()["total"] == 1

    async def test_seeker_can_start_conversation_and_recruiter_can_list_it(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, seeker_token, job_id, detail = await create_conversation(
            client,
            test_recruiter_data,
            test_user_data,
            db_session,
        )

        assert detail["job_id"] == job_id
        assert len(detail["messages"]) == 1
        assert detail["messages"][0]["content"] == "您好，我对这个岗位很感兴趣。"

        seeker_list = await client.get(
            "/api/v1/messages/conversations",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert seeker_list.status_code == 200
        assert seeker_list.json()["total"] == 1

        recruiter_list = await client.get(
            "/api/v1/messages/conversations",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_list.status_code == 200
        assert recruiter_list.json()["total"] == 1
        listed = recruiter_list.json()["items"][0]
        assert listed["lead_status"] == "messaged"
        assert listed["lead_status_label"] == "已沟通"
        assert listed["application_id"] is None

    async def test_conversation_list_reports_application_and_exchange_lead_status(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, seeker_token, job_id, detail = await create_conversation(
            client,
            test_recruiter_data,
            test_user_data,
            db_session,
        )
        conversation_id = detail["id"]

        await upload_resume(client, seeker_token)
        apply_response = await client.post(
            "/api/v1/applications",
            json={"job_id": job_id, "cover_message": "I would like to apply."},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert apply_response.status_code == 201
        application_id = apply_response.json()["id"]

        recruiter_list_after_apply = await client.get(
            "/api/v1/messages/conversations",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_list_after_apply.status_code == 200
        applied_item = recruiter_list_after_apply.json()["items"][0]
        assert applied_item["lead_status"] == "applied"
        assert applied_item["lead_status_label"] == "已投递"
        assert applied_item["application_id"] == application_id
        assert applied_item["application_status"] == "submitted"

        request_response = await client.post(
            "/api/v1/messages/contact-exchanges",
            json={"conversation_id": conversation_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert request_response.status_code == 201
        exchange_id = request_response.json()["id"]

        recruiter_pending_list = await client.get(
            "/api/v1/messages/conversations",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_pending_list.status_code == 200
        recruiter_pending = recruiter_pending_list.json()["items"][0]
        assert recruiter_pending["lead_status"] == "contact_needs_review"
        assert recruiter_pending["lead_status_label"] == "等你确认"

        seeker_pending_list = await client.get(
            "/api/v1/messages/conversations",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert seeker_pending_list.status_code == 200
        seeker_pending = seeker_pending_list.json()["items"][0]
        assert seeker_pending["lead_status"] == "contact_waiting"
        assert seeker_pending["lead_status_label"] == "等待对方同意"

        accept_response = await client.post(
            f"/api/v1/messages/contact-exchanges/{exchange_id}/review",
            json={"action": "accept"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert accept_response.status_code == 200

        recruiter_accepted_list = await client.get(
            "/api/v1/messages/conversations",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_accepted_list.status_code == 200
        accepted = recruiter_accepted_list.json()["items"][0]
        assert accepted["lead_status"] == "contact_exchanged"
        assert accepted["lead_status_label"] == "已交换联系方式"

    async def test_message_contact_info_is_masked(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        _, seeker_token, _, detail = await create_conversation(
            client,
            test_recruiter_data,
            test_user_data,
            db_session,
        )
        conversation_id = detail["id"]

        response = await client.post(
            f"/api/v1/messages/conversations/{conversation_id}/messages",
            json={"content": "我的手机号是13800138000，微信vx123456"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 200
        latest = response.json()["messages"][-1]
        assert "[联系方式已屏蔽]" in latest["content"]
        assert latest["moderation_status"] == "masked"
        assert latest["original_content"] == "我的手机号是13800138000，微信vx123456"

    async def test_contact_exchange_accept_returns_contacts(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, seeker_token, _, detail = await create_conversation(
            client,
            test_recruiter_data,
            test_user_data,
            db_session,
        )
        conversation_id = detail["id"]

        request_response = await client.post(
            "/api/v1/messages/contact-exchanges",
            json={"conversation_id": conversation_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert request_response.status_code == 201
        exchange_id = request_response.json()["id"]
        assert request_response.json()["status"] == "pending"

        review_response = await client.post(
            f"/api/v1/messages/contact-exchanges/{exchange_id}/review",
            json={"action": "accept"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert review_response.status_code == 200
        data = review_response.json()
        assert data["status"] == "accepted"
        assert len(data["contacts"]) == 2
        roles = {item["role"] for item in data["contacts"]}
        assert roles == {"seeker", "recruiter"}
        recruiter_contact = next(item for item in data["contacts"] if item["role"] == "recruiter")
        seeker_contact = next(item for item in data["contacts"] if item["role"] == "seeker")
        assert recruiter_contact["company_name"] is None
        assert recruiter_contact["phone"] is None
        assert recruiter_contact["email"] is None
        assert seeker_contact["phone"] == test_user_data["phone"]

        detail_response = await client.get(
            f"/api/v1/messages/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert detail_response.status_code == 200
        accepted_exchange = detail_response.json()["contact_exchange"]
        assert accepted_exchange["status"] == "accepted"
        assert len(accepted_exchange["contacts"]) == 2

    async def test_contact_exchange_respects_recruiter_and_seeker_visibility(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        certification = {
            "company_name": "Visibility Test Co",
            "unified_social_credit_code": "91330100MA2KABCD1A",
            "legal_representative": "Owner",
            "registered_address": "Hangzhou Test Road 100",
            "license_file_url": "mock://licenses/visibility.pdf",
            "license_file_name": "license.pdf",
            "work_email": "hr@visibility.example.com",
            "applicant_phone": "057188888888",
            "applicant_wechat": "hr_visibility",
        }
        admin_token = await approve_current_recruiter_certification_with_payload(
            client,
            db_session,
            recruiter_token,
            certification,
        )
        create_response = await client.post(
            "/api/v1/jobs/me",
            json={
                **job_payload(),
                "company_display_mode": "company_name",
                "contact_phone_public": True,
                "contact_email_public": True,
                "contact_wechat_public": True,
            },
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert create_response.status_code == 201
        job_id = create_response.json()["id"]
        await client.post(
            f"/api/v1/jobs/admin/{job_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        seeker_token = await register_and_get_token(client, test_user_data)
        profile_response = await client.put(
            "/api/v1/seeker-profiles/me",
            json={
                "real_name": "Candidate Visible",
                "phone_public": False,
                "email": "candidate@example.com",
                "wechat": "candidate_wx",
                "email_public": True,
                "wechat_public": True,
            },
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert profile_response.status_code == 200

        conversation_response = await client.post(
            "/api/v1/messages/conversations/open",
            json={"job_id": job_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert conversation_response.status_code == 201
        conversation_id = conversation_response.json()["id"]
        request_response = await client.post(
            "/api/v1/messages/contact-exchanges",
            json={"conversation_id": conversation_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert request_response.status_code == 201
        exchange_id = request_response.json()["id"]

        review_response = await client.post(
            f"/api/v1/messages/contact-exchanges/{exchange_id}/review",
            json={"action": "accept"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert review_response.status_code == 200
        recruiter_contact = next(item for item in review_response.json()["contacts"] if item["role"] == "recruiter")
        seeker_contact = next(item for item in review_response.json()["contacts"] if item["role"] == "seeker")
        assert recruiter_contact["display_name"] == certification["company_name"]
        assert recruiter_contact["company_name"] == certification["company_name"]
        assert recruiter_contact["phone"] == certification["applicant_phone"]
        assert recruiter_contact["email"] == certification["work_email"]
        assert recruiter_contact["wechat"] == certification["applicant_wechat"]
        assert seeker_contact["display_name"] == "Candidate Visible"
        assert seeker_contact["phone"] is None
        assert seeker_contact["email"] == "candidate@example.com"
        assert seeker_contact["wechat"] == "candidate_wx"

    async def test_contact_exchange_stats_track_successful_connections(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, seeker_token, _, detail = await create_conversation(
            client,
            test_recruiter_data,
            test_user_data,
            db_session,
        )
        conversation_id = detail["id"]

        initial_stats = await client.get(
            "/api/v1/messages/contact-exchanges/stats/summary",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert initial_stats.status_code == 200
        assert initial_stats.json() == {
            "accepted_count": 0,
            "pending_count": 0,
            "declined_count": 0,
            "total_count": 0,
        }

        request_response = await client.post(
            "/api/v1/messages/contact-exchanges",
            json={"conversation_id": conversation_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert request_response.status_code == 201
        exchange_id = request_response.json()["id"]

        pending_stats = await client.get(
            "/api/v1/messages/contact-exchanges/stats/summary",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert pending_stats.status_code == 200
        assert pending_stats.json()["pending_count"] == 1
        assert pending_stats.json()["accepted_count"] == 0
        assert pending_stats.json()["total_count"] == 1

        review_response = await client.post(
            f"/api/v1/messages/contact-exchanges/{exchange_id}/review",
            json={"action": "accept"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert review_response.status_code == 200

        accepted_stats = await client.get(
            "/api/v1/messages/contact-exchanges/stats/summary",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert accepted_stats.status_code == 200
        assert accepted_stats.json()["accepted_count"] == 1
        assert accepted_stats.json()["pending_count"] == 0
        assert accepted_stats.json()["total_count"] == 1

    async def test_admin_can_view_platform_contact_exchange_stats(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, seeker_token, _, detail = await create_conversation(
            client,
            test_recruiter_data,
            test_user_data,
            db_session,
        )
        conversation_id = detail["id"]
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"phone": "13700137001", "password": "Admin1234"},
        )
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]

        request_response = await client.post(
            "/api/v1/messages/contact-exchanges",
            json={"conversation_id": conversation_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert request_response.status_code == 201
        exchange_id = request_response.json()["id"]

        await client.post(
            f"/api/v1/messages/contact-exchanges/{exchange_id}/review",
            json={"action": "accept"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        response = await client.get(
            "/api/v1/messages/contact-exchanges/stats/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.json()["accepted_count"] == 1
        assert response.json()["pending_count"] == 0
        assert response.json()["declined_count"] == 0
        assert response.json()["total_count"] == 1

    async def test_seeker_cannot_view_contact_exchange_stats(
        self,
        client: AsyncClient,
        test_user_data,
    ):
        seeker_token = await register_and_get_token(client, test_user_data)

        response = await client.get(
            "/api/v1/messages/contact-exchanges/stats/summary",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 403

    async def test_contact_exchange_hides_seeker_phone_when_profile_phone_is_private(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, seeker_token, _, detail = await create_conversation(
            client,
            test_recruiter_data,
            test_user_data,
            db_session,
        )
        conversation_id = detail["id"]

        profile_response = await client.put(
            "/api/v1/seeker-profiles/me",
            json={
                "real_name": "测试求职者",
                "target_position": "前端开发",
                "city": "上海",
                "phone_public": False,
            },
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert profile_response.status_code == 200
        assert profile_response.json()["phone_public"] is False

        request_response = await client.post(
            "/api/v1/messages/contact-exchanges",
            json={"conversation_id": conversation_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert request_response.status_code == 201
        exchange_id = request_response.json()["id"]

        review_response = await client.post(
            f"/api/v1/messages/contact-exchanges/{exchange_id}/review",
            json={"action": "accept"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert review_response.status_code == 200
        seeker_contact = next(item for item in review_response.json()["contacts"] if item["role"] == "seeker")
        assert seeker_contact["phone"] is None

    async def test_requester_cannot_review_own_exchange(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        _, seeker_token, _, detail = await create_conversation(
            client,
            test_recruiter_data,
            test_user_data,
            db_session,
        )
        conversation_id = detail["id"]
        request_response = await client.post(
            "/api/v1/messages/contact-exchanges",
            json={"conversation_id": conversation_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        exchange_id = request_response.json()["id"]

        review_response = await client.post(
            f"/api/v1/messages/contact-exchanges/{exchange_id}/review",
            json={"action": "accept"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert review_response.status_code == 400
        assert "own contact exchange" in review_response.json()["detail"]
