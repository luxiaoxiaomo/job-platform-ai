"""
Notification event API tests.
"""
from datetime import datetime

from httpx import AsyncClient

from app.core.config import settings
from app.modules.notification.repository import NotificationRepository
from app.modules.notification.service import NotificationService
from tests.test_api.test_applications import create_active_job, upload_resume
from tests.test_api.test_company_certifications import register_and_get_token
from tests.test_api.test_jobs import approve_current_recruiter_certification, job_payload


async def _list_notifications(client: AsyncClient, token: str) -> list[dict]:
    response = await client.get(
        "/api/v1/notifications",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    return response.json()["items"]


class TestNotificationEvents:
    async def test_create_or_update_is_idempotent_by_dedupe_key(
        self,
        db_session,
    ):
        first = await NotificationService.create_or_update(
            db_session,
            recipient_id=1,
            type_="system",
            title="First",
            detail="first detail",
            dedupe_key="unit:test",
        )
        second = await NotificationService.create_or_update(
            db_session,
            recipient_id=1,
            type_="system",
            title="Second",
            detail="second detail",
            dedupe_key="unit:test",
        )

        items, total = await NotificationRepository.list_for_user(db_session, recipient_id=1)
        assert first.id == second.id
        assert total == 1
        assert items[0].title == "Second"
        assert items[0].detail == "second detail"

    async def test_job_review_writes_recruiter_notification(
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

        review_response = await client.post(
            f"/api/v1/jobs/admin/{job_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert review_response.status_code == 200
        items = await _list_notifications(client, recruiter_token)
        notification = next(item for item in items if item["type"] == "job_review")
        assert notification["title"] == "岗位「前端开发工程师」审核通过"
        assert notification["action_url"] == f"/recruiter/job/{job_id}"
        assert notification["payload"]["job_id"] == job_id
        assert notification["payload"]["review_action"] == "approve"
        assert notification["read"] is False

    async def test_message_writes_counterparty_notification(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        test_user_data,
    ):
        recruiter_token, job_id = await create_active_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)

        seeker_message = await client.post(
            "/api/v1/messages/messages",
            json={"job_id": job_id, "content": "我想了解这个岗位"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert seeker_message.status_code == 201
        conversation_id = seeker_message.json()["id"]
        recruiter_items = await _list_notifications(client, recruiter_token)
        recruiter_notification = next(item for item in recruiter_items if item["type"] == "message")
        assert recruiter_notification["action_url"] == f"/recruiter/chat/{conversation_id}"
        assert recruiter_notification["payload"]["conversation_id"] == conversation_id
        assert recruiter_notification["payload"]["sender_role"] == "seeker"

        recruiter_reply = await client.post(
            f"/api/v1/messages/conversations/{conversation_id}/messages",
            json={"content": "可以，欢迎投递简历。"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert recruiter_reply.status_code == 200
        seeker_items = await _list_notifications(client, seeker_token)
        seeker_notification = next(item for item in seeker_items if item["type"] == "message")
        assert seeker_notification["action_url"] == f"/seeker/chat/{conversation_id}"
        assert seeker_notification["payload"]["conversation_id"] == conversation_id
        assert seeker_notification["payload"]["sender_role"] == "recruiter"

    async def test_application_and_status_update_write_notifications(
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
            json={"job_id": job_id, "cover_message": "我想投递这个岗位。"},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert apply_response.status_code == 201
        application_id = apply_response.json()["id"]
        recruiter_items = await _list_notifications(client, recruiter_token)
        application_notification = next(item for item in recruiter_items if item["type"] == "application")
        assert application_notification["action_url"] == f"/recruiter/applications/{application_id}"
        assert application_notification["payload"]["application_id"] == application_id
        assert application_notification["payload"]["job_id"] == job_id
        assert application_notification["payload"]["status"] == "submitted"

        status_response = await client.post(
            f"/api/v1/applications/{application_id}/status",
            json={"status": "interview_invited"},
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert status_response.status_code == 200
        seeker_items = await _list_notifications(client, seeker_token)
        status_notification = next(item for item in seeker_items if item["type"] == "application_status")
        assert status_notification["action_url"] == f"/seeker/applications?applicationId={application_id}"
        assert status_notification["payload"]["application_id"] == application_id
        assert status_notification["payload"]["from_status"] == "submitted"
        assert status_notification["payload"]["to_status"] == "interview_invited"

    async def test_external_notification_creates_pending_push_task_within_send_window(
        self,
        db_session,
        monkeypatch,
    ):
        fixed_now = datetime(2026, 6, 19, 10, 30, 0)
        monkeypatch.setattr(NotificationService, "_push_now", staticmethod(lambda: fixed_now))

        notification = await NotificationService.create_or_update(
            db_session,
            recipient_id=1,
            type_="message",
            title="New message",
            detail="Please review",
            action_url="/recruiter/chat/1",
            payload={"conversation_id": 1},
            dedupe_key="message:push:test:1",
        )

        tasks, total = await NotificationRepository.list_push_tasks(db_session, recipient_id=1)
        assert total == 1
        task = tasks[0]
        assert task.notification_id == notification.id
        assert task.status == "pending"
        assert task.scheduled_at == fixed_now
        assert task.daily_sequence == 1
        assert task.reason == "within_window"
        assert task.send_window_start == "08:00"
        assert task.send_window_end == "21:00"

    async def test_push_tasks_respect_daily_immediate_limit(
        self,
        db_session,
        monkeypatch,
    ):
        fixed_now = datetime(2026, 6, 19, 15, 0, 0)
        monkeypatch.setattr(NotificationService, "_push_now", staticmethod(lambda: fixed_now))

        for index in range(6):
            await NotificationService.create_or_update(
                db_session,
                recipient_id=1,
                type_="message",
                title=f"New message {index}",
                detail="Please review",
                dedupe_key=f"message:push:test:limit:{index}",
            )

        tasks, total = await NotificationRepository.list_push_tasks(db_session, recipient_id=1)
        assert total == 6
        assert [task.status for task in tasks[:5]] == ["pending"] * 5
        assert [task.daily_sequence for task in tasks[:5]] == [1, 2, 3, 4, 5]
        assert tasks[5].status == "digest_placeholder"
        assert tasks[5].daily_sequence is None
        assert tasks[5].reason == "daily_limit_exceeded"
        assert tasks[5].scheduled_at == datetime(2026, 6, 20, 8, 0, 0)

    async def test_external_notification_outside_send_window_is_deferred(
        self,
        db_session,
        monkeypatch,
    ):
        fixed_now = datetime(2026, 6, 19, 22, 15, 0)
        monkeypatch.setattr(NotificationService, "_push_now", staticmethod(lambda: fixed_now))

        await NotificationService.create_or_update(
            db_session,
            recipient_id=1,
            type_="application",
            title="New application",
            dedupe_key="application:push:test:deferred",
        )

        tasks, total = await NotificationRepository.list_push_tasks(db_session, recipient_id=1)
        assert total == 1
        assert tasks[0].status == "deferred"
        assert tasks[0].scheduled_at == datetime(2026, 6, 20, 8, 0, 0)
        assert tasks[0].reason == "outside_send_window"

    async def test_push_task_endpoint_returns_current_user_tasks(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        monkeypatch,
    ):
        fixed_now = datetime(2026, 6, 19, 9, 0, 0)
        monkeypatch.setattr(NotificationService, "_push_now", staticmethod(lambda: fixed_now))
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        user_response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert user_response.status_code == 200
        recruiter_id = user_response.json()["id"]

        await NotificationService.create_or_update(
            db_session,
            recipient_id=recruiter_id,
            type_="message",
            title="New message",
            dedupe_key="message:push:test:endpoint",
        )
        await NotificationService.create_or_update(
            db_session,
            recipient_id=recruiter_id + 1000,
            type_="message",
            title="Other user's message",
            dedupe_key="message:push:test:other",
        )

        response = await client.get(
            "/api/v1/notifications/push-tasks",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["recipient_id"] == recruiter_id
        assert data["items"][0]["status"] == "pending"
        assert data["items"][0]["reason"] == "within_window"

    async def test_admin_can_manage_push_tasks(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        monkeypatch,
    ):
        fixed_now = datetime(2026, 6, 19, 9, 30, 0)
        monkeypatch.setattr(NotificationService, "_push_now", staticmethod(lambda: fixed_now))
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)
        user_response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        recipient_id = user_response.json()["id"]

        await NotificationService.create_or_update(
            db_session,
            recipient_id=recipient_id,
            type_="message",
            title="Admin managed push",
            dedupe_key="message:push:test:admin",
        )

        list_response = await client.get(
            "/api/v1/notifications/admin/push-tasks",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert list_response.status_code == 200
        data = list_response.json()
        task = next(item for item in data["items"] if item["recipient_id"] == recipient_id)
        assert task["status"] == "pending"

        sent_response = await client.post(
            f"/api/v1/notifications/admin/push-tasks/{task['id']}/status",
            json={"status": "sent"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert sent_response.status_code == 200
        assert sent_response.json()["status"] == "sent"
        assert sent_response.json()["sent_at"] is not None

        sent_list = await client.get(
            "/api/v1/notifications/admin/push-tasks",
            params={"status": "sent"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert sent_list.status_code == 200
        assert any(item["id"] == task["id"] for item in sent_list.json()["items"])

        failed_response = await client.post(
            f"/api/v1/notifications/admin/push-tasks/{task['id']}/status",
            json={"status": "failed", "error_message": "manual test failure"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert failed_response.status_code == 200
        failed = failed_response.json()
        assert failed["status"] == "failed"
        assert failed["failed_at"] is not None
        assert failed["error_message"] == "manual test failure"

    async def test_admin_push_worker_marks_due_tasks_and_digest_sent(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        monkeypatch,
    ):
        schedule_now = datetime(2026, 6, 19, 9, 0, 0)
        run_now = datetime(2026, 6, 20, 8, 30, 0)
        monkeypatch.setattr(NotificationService, "_push_now", staticmethod(lambda: schedule_now))
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)
        user_response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        recipient_id = user_response.json()["id"]

        for index in range(6):
            await NotificationService.create_or_update(
                db_session,
                recipient_id=recipient_id,
                type_="message",
                title=f"Worker task {index}",
                detail=f"Detail {index}",
                dedupe_key=f"message:push:test:worker:{index}",
            )

        before_items, before_total = await NotificationRepository.list_push_tasks(db_session, recipient_id=recipient_id)
        assert before_total == 6
        assert [item.status for item in before_items].count("digest_placeholder") == 1

        monkeypatch.setattr(NotificationService, "_push_now", staticmethod(lambda: run_now))
        worker_response = await client.post(
            "/api/v1/notifications/admin/push-tasks/run-worker",
            params={"limit": 20},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert worker_response.status_code == 200
        data = worker_response.json()
        assert data["processed_count"] == 6
        assert data["sent_count"] == 5
        assert data["digest_count"] == 1
        assert data["failed_count"] == 0
        assert all(item["status"] == "sent" for item in data["items"])
        assert all(item["attempt_count"] == 1 for item in data["items"])
        assert all(item["payload"]["push_provider"]["provider"] == "wechat_template_dry_run" for item in data["items"])
        digest = next(item for item in data["items"] if item["payload"].get("digest_source_status") == "digest_placeholder")
        assert digest["sent_at"] is not None
        assert digest["payload"]["digest_generated_at"].startswith("2026-06-20T08:30:00")

    async def test_live_wechat_worker_fails_without_bound_openid(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
        monkeypatch,
    ):
        fixed_now = datetime(2026, 6, 19, 9, 30, 0)
        monkeypatch.setattr(NotificationService, "_push_now", staticmethod(lambda: fixed_now))
        monkeypatch.setattr(settings, "WECHAT_PUSH_MODE", "live")
        monkeypatch.setattr(settings, "WECHAT_APP_ID", "wx-test")
        monkeypatch.setattr(settings, "WECHAT_APP_SECRET", "secret-test")
        monkeypatch.setattr(settings, "WECHAT_TEMPLATE_MESSAGE", "template-message")
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)
        user_response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        recipient_id = user_response.json()["id"]

        await NotificationService.create_or_update(
            db_session,
            recipient_id=recipient_id,
            type_="message",
            title="Needs WeChat OpenID",
            detail="This should stay as in-app fallback.",
            dedupe_key="message:push:test:missing-openid",
        )

        worker_response = await client.post(
            "/api/v1/notifications/admin/push-tasks/run-worker",
            params={"limit": 5},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert worker_response.status_code == 200
        data = worker_response.json()
        assert data["processed_count"] == 1
        assert data["sent_count"] == 0
        assert data["failed_count"] == 1
        item = data["items"][0]
        assert item["status"] == "failed"
        assert item["attempt_count"] == 1
        assert item["error_message"].startswith("Recipient has not bound a WeChat OpenID")
        assert item["payload"]["push_provider"]["error_code"] == "missing_wechat_openid"
