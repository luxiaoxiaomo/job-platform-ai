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


async def approve_current_recruiter_certification_with_payload(
    client: AsyncClient,
    db_session,
    recruiter_token: str,
    payload: dict,
) -> str:
    await client.post(
        "/api/v1/company-certifications/me",
        json=payload,
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

    async def test_certified_recruiter_can_link_job_to_standard_position(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
    ):
        token = await register_and_get_token(client, test_recruiter_data)
        admin_token = await approve_current_recruiter_certification(client, db_session, token)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        recruiter_headers = {"Authorization": f"Bearer {token}"}
        position_response = await client.post(
            "/api/v1/base-data/standard-positions",
            json={
                "name": "前端开发工程师",
                "category": "技术研发",
                "aliases": ["前端工程师", "React 工程师"],
            },
            headers=admin_headers,
        )
        assert position_response.status_code == 201
        standard_position = position_response.json()

        response = await client.post(
            "/api/v1/jobs/me",
            json={**job_payload(), "standard_position_id": standard_position["id"]},
            headers=recruiter_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["standard_position_id"] == standard_position["id"]
        assert data["standard_position_name"] == "前端开发工程师"

        list_response = await client.get("/api/v1/jobs/me", headers=recruiter_headers)
        assert list_response.status_code == 200
        assert list_response.json()["items"][0]["standard_position_id"] == standard_position["id"]

    async def test_certified_recruiter_can_link_job_to_tag_library_items(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
    ):
        token = await register_and_get_token(client, test_recruiter_data)
        admin_token = await approve_current_recruiter_certification(client, db_session, token)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        recruiter_headers = {"Authorization": f"Bearer {token}"}
        tag_response = await client.post(
            "/api/v1/base-data/tags",
            json={"name": "React", "category": "技能", "color": "#61dafb"},
            headers=admin_headers,
        )
        assert tag_response.status_code == 201
        tag = tag_response.json()

        response = await client.post(
            "/api/v1/jobs/me",
            json={**job_payload(), "tag_ids": [tag["id"]]},
            headers=recruiter_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["tags"] == ["React"]
        assert data["tag_refs"] == [
            {"id": tag["id"], "name": "React", "category": "技能", "color": "#61dafb"}
        ]

        list_response = await client.get("/api/v1/jobs/me", headers=recruiter_headers)
        assert list_response.status_code == 200
        assert list_response.json()["items"][0]["tag_refs"][0]["id"] == tag["id"]

    async def test_recruiter_cannot_link_job_to_missing_tag_library_item(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
    ):
        token = await register_and_get_token(client, test_recruiter_data)
        await approve_current_recruiter_certification(client, db_session, token)

        response = await client.post(
            "/api/v1/jobs/me",
            json={**job_payload(), "tag_ids": [999999]},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Tag not found"

    async def test_recruiter_cannot_link_job_to_missing_standard_position(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
    ):
        token = await register_and_get_token(client, test_recruiter_data)
        await approve_current_recruiter_certification(client, db_session, token)

        response = await client.post(
            "/api/v1/jobs/me",
            json={**job_payload(), "standard_position_id": 999999},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Standard position not found"

    async def test_recruiter_can_save_draft_and_submit_for_review(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
    ):
        token = await register_and_get_token(client, test_recruiter_data)
        await approve_current_recruiter_certification(client, db_session, token)

        response = await client.post(
            "/api/v1/jobs/me",
            json={**job_payload(), "status": "draft"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "draft"
        assert data["published_at"] is None

        submit_response = await client.post(
            f"/api/v1/jobs/me/{data['id']}/submit-review",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert submit_response.status_code == 200
        assert submit_response.json()["status"] == "pending"
        assert submit_response.json()["reject_reason"] is None

    async def test_recruiter_can_resubmit_rejected_job_for_review(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)
        create_response = await client.post(
            "/api/v1/jobs/me",
            json=job_payload(),
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        job_id = create_response.json()["id"]

        reject_response = await client.post(
            f"/api/v1/jobs/admin/{job_id}/review",
            json={"action": "reject", "reject_reason": "描述不够完整"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert reject_response.status_code == 200
        assert reject_response.json()["status"] == "rejected"

        submit_response = await client.post(
            f"/api/v1/jobs/me/{job_id}/submit-review",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert submit_response.status_code == 200
        data = submit_response.json()
        assert data["status"] == "pending"
        assert data["reject_reason"] is None
        assert data["reviewer_id"] is None
        assert data["reviewed_at"] is None

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

    async def test_public_jobs_endpoint_does_not_require_auth(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
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

        public_response = await client.get("/api/v1/jobs/public")

        assert public_response.status_code == 200
        data = public_response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == job_id
        assert data["items"][0]["conversation_count"] == 0

        detail_response = await client.get(f"/api/v1/jobs/public/{job_id}")
        assert detail_response.status_code == 200
        assert detail_response.json()["id"] == job_id
        assert detail_response.json()["conversation_count"] == 0

    async def test_public_job_detail_uses_public_contact_visibility(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        certification = {
            **certification_payload(),
            "work_email": "hr@yichuang.example.com",
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
                "contact_email_public": True,
                "contact_phone_public": False,
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

        detail_response = await client.get(f"/api/v1/jobs/public/{job_id}")

        assert detail_response.status_code == 200
        data = detail_response.json()
        assert data["company_display_mode"] == "company_name"
        assert data["recruiter_display_name"] == certification["company_name"]
        assert data["public_contact"]["company_name"] == certification["company_name"]
        assert data["public_contact"]["email"] == certification["work_email"]
        assert data["public_contact"]["phone"] is None
        assert data["public_contact"]["wechat"] == certification["applicant_wechat"]

    async def test_recruiter_can_update_visibility_without_resubmitting_active_job(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        certification = {
            **certification_payload(),
            "work_email": "hr@yichuang.example.com",
        }
        admin_token = await approve_current_recruiter_certification_with_payload(
            client,
            db_session,
            recruiter_token,
            certification,
        )
        create_response = await client.post(
            "/api/v1/jobs/me",
            json=job_payload(),
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert create_response.status_code == 201
        job_id = create_response.json()["id"]
        await client.post(
            f"/api/v1/jobs/admin/{job_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        update_response = await client.put(
            f"/api/v1/jobs/me/{job_id}",
            json={"company_display_mode": "company_name", "contact_email_public": True},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["status"] == "active"
        assert data["company_display_mode"] == "company_name"
        assert data["public_contact"]["email"] == certification["work_email"]

    async def test_public_job_detail_increments_view_count(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)
        create_response = await client.post(
            "/api/v1/jobs/me",
            json=job_payload(),
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        job_id = create_response.json()["id"]
        assert create_response.json()["view_count"] == 0

        await client.post(
            f"/api/v1/jobs/admin/{job_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        list_response = await client.get("/api/v1/jobs/public")
        assert list_response.status_code == 200
        assert list_response.json()["items"][0]["view_count"] == 0

        first_detail = await client.get(f"/api/v1/jobs/public/{job_id}")
        second_detail = await client.get(f"/api/v1/jobs/public/{job_id}")

        assert first_detail.status_code == 200
        assert first_detail.json()["view_count"] == 1
        assert second_detail.status_code == 200
        assert second_detail.json()["view_count"] == 2

        recruiter_jobs = await client.get(
            "/api/v1/jobs/me",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert recruiter_jobs.status_code == 200
        assert recruiter_jobs.json()["items"][0]["view_count"] == 2

    async def test_public_job_detail_records_authenticated_seeker_visitors(
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

        await client.post(
            f"/api/v1/jobs/admin/{job_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        anonymous_detail = await client.get(f"/api/v1/jobs/public/{job_id}")
        assert anonymous_detail.status_code == 200

        seeker_token = await register_and_get_token(client, test_user_data)
        first_detail = await client.get(
            f"/api/v1/jobs/public/{job_id}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        second_detail = await client.get(
            f"/api/v1/jobs/public/{job_id}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert first_detail.status_code == 200
        assert second_detail.status_code == 200
        assert second_detail.json()["view_count"] == 3

        conversation_response = await client.post(
            "/api/v1/messages/conversations/open",
            json={"job_id": job_id},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert conversation_response.status_code == 201

        visitors_response = await client.get(
            f"/api/v1/jobs/me/{job_id}/visitors",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert visitors_response.status_code == 200
        visitors = visitors_response.json()
        assert visitors["job_id"] == job_id
        assert visitors["total_views"] == 3
        assert visitors["unique_visitors"] == 1
        assert visitors["total"] == 1
        visitor = visitors["items"][0]
        assert visitor["seeker_display_name"] == test_user_data["display_name"]
        assert visitor["view_count"] == 2
        assert visitor["has_conversation"] is True
        assert visitor["has_application"] is False
        assert visitor["high_intent"] is True
        assert visitor["intent_score"] >= 70
        assert "已咨询" in visitor["tags"]

    async def test_seeker_history_favorites_and_subscriptions_are_real(
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
        await client.post(
            f"/api/v1/jobs/admin/{job_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        seeker_token = await register_and_get_token(client, test_user_data)
        for _ in range(2):
            detail_response = await client.get(
                f"/api/v1/jobs/public/{job_id}",
                headers={"Authorization": f"Bearer {seeker_token}"},
            )
            assert detail_response.status_code == 200

        history_response = await client.get(
            "/api/v1/jobs/seeker/history",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert history_response.status_code == 200
        history = history_response.json()
        assert history["total"] == 1
        assert history["items"][0]["job"]["id"] == job_id
        assert history["items"][0]["view_count"] == 2
        assert history["items"][0]["is_favorited"] is False

        favorite_response = await client.post(
            f"/api/v1/jobs/seeker/favorites/{job_id}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert favorite_response.status_code == 201
        assert favorite_response.json()["job"]["id"] == job_id

        duplicate_favorite = await client.post(
            f"/api/v1/jobs/seeker/favorites/{job_id}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert duplicate_favorite.status_code == 201
        assert duplicate_favorite.json()["id"] == favorite_response.json()["id"]

        favorites_response = await client.get(
            "/api/v1/jobs/seeker/favorites",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert favorites_response.status_code == 200
        favorites = favorites_response.json()
        assert favorites["total"] == 1
        assert favorites["items"][0]["job"]["id"] == job_id

        history_after_favorite = await client.get(
            "/api/v1/jobs/seeker/history",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert history_after_favorite.json()["items"][0]["is_favorited"] is True

        subscription_response = await client.post(
            "/api/v1/jobs/seeker/subscriptions",
            json={
                "keywords": ["React"],
                "city": "深圳",
                "salary_min": 10,
                "active": True,
            },
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert subscription_response.status_code == 201
        subscription = subscription_response.json()
        assert subscription["keywords"] == ["React"]
        assert subscription["match_count"] == 1
        assert subscription["matched_jobs"][0]["id"] == job_id

        notifications_response = await client.get(
            "/api/v1/jobs/seeker/notifications",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert notifications_response.status_code == 200
        notifications = notifications_response.json()
        assert notifications["total"] == 1
        assert notifications["items"][0]["type"] == "match"
        assert notifications["items"][0]["subscription_id"] == subscription["id"]
        assert notifications["items"][0]["subscription_name"] == subscription["name"]
        assert notifications["items"][0]["match_count"] == 1
        assert notifications["items"][0]["matched_job_ids"] == [job_id]
        assert "前端开发工程师" in notifications["items"][0]["detail"]

        persisted_notifications = await client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert persisted_notifications.status_code == 200
        persisted = persisted_notifications.json()
        assert persisted["total"] == 1
        assert persisted["unread_count"] == 1
        persisted_item = persisted["items"][0]
        assert persisted_item["type"] == "match"
        assert persisted_item["read"] is False
        assert persisted_item["payload"]["subscription_id"] == subscription["id"]
        assert persisted_item["payload"]["matched_job_ids"] == [job_id]

        unread_count = await client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert unread_count.status_code == 200
        assert unread_count.json()["unread_count"] == 1

        match_unread_count = await client.get(
            "/api/v1/notifications/unread-count",
            params={"type": "match"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert match_unread_count.status_code == 200
        assert match_unread_count.json()["unread_count"] == 1

        mark_match_read = await client.post(
            "/api/v1/notifications/types/match/read",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert mark_match_read.status_code == 200
        assert mark_match_read.json()["unread_count"] == 0

        after_match_read_count = await client.get(
            "/api/v1/notifications/unread-count",
            params={"type": "match"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert after_match_read_count.status_code == 200
        assert after_match_read_count.json()["unread_count"] == 0

        mark_read = await client.post(
            f"/api/v1/notifications/{persisted_item['id']}/read",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert mark_read.status_code == 200
        assert mark_read.json()["unread_count"] == 0

        after_read = await client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert after_read.status_code == 200
        assert after_read.json()["total"] == 1
        assert after_read.json()["unread_count"] == 0
        assert after_read.json()["items"][0]["read"] is True

        mark_all = await client.post(
            "/api/v1/notifications/read-all",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert mark_all.status_code == 200
        assert mark_all.json()["ok"] is True
        assert mark_all.json()["unread_count"] == 0

        update_response = await client.put(
            f"/api/v1/jobs/seeker/subscriptions/{subscription['id']}",
            json={"active": False},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["active"] is False

        list_subscriptions = await client.get(
            "/api/v1/jobs/seeker/subscriptions",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert list_subscriptions.status_code == 200
        assert list_subscriptions.json()["total"] == 1

        delete_subscription = await client.delete(
            f"/api/v1/jobs/seeker/subscriptions/{subscription['id']}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert delete_subscription.status_code == 200

        remove_favorite = await client.delete(
            f"/api/v1/jobs/seeker/favorites/{job_id}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert remove_favorite.status_code == 200

    async def test_public_job_detail_hides_pending_jobs(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        await approve_current_recruiter_certification(client, db_session, recruiter_token)
        create_response = await client.post(
            "/api/v1/jobs/me",
            json=job_payload(),
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        job_id = create_response.json()["id"]

        detail_response = await client.get(f"/api/v1/jobs/public/{job_id}")

        assert detail_response.status_code == 404

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
岗位职责：负责招聘平台前端页面开发、接口联调和性能优化。
任职要求：熟悉 React 和 JavaScript，有真实项目交付经验。
福利待遇：五险一金、带薪年假。
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
岗位职责：负责招聘平台后端接口开发、数据建模和服务稳定性优化。
任职要求：熟悉 Python 和 FastAPI，理解数据库设计和接口鉴权。
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
