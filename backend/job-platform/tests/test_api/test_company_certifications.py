"""
Enterprise certification API tests.
"""
import pytest
from httpx import AsyncClient


async def register_and_get_token(client: AsyncClient, user_data: dict) -> str:
    code_response = await client.post(
        "/api/v1/auth/send-verification-code",
        params={"phone": user_data["phone"]},
    )
    code = code_response.json()["code"]
    response = await client.post(
        "/api/v1/auth/register",
        json={**user_data, "verification_code": code},
    )
    return response.json()["access_token"]


async def create_admin_token(client: AsyncClient, db_session) -> str:
    from app.core.security import hash_password
    from app.modules.user.models import User
    from app.utils.encryption import encryptor
    from app.utils.phone_hash import hash_phone

    admin_phone = "13700137001"
    admin = User(
        phone_hash=hash_phone(admin_phone),
        phone_encrypted=encryptor.encrypt(admin_phone),
        password_hash=hash_password("Admin1234"),
        display_name="认证管理员",
        role="admin",
        status="active",
    )
    db_session.add(admin)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"phone": admin_phone, "password": "Admin1234"},
    )
    return response.json()["access_token"]


def certification_payload() -> dict:
    return {
        "company_name": "杭州毅创越新信息咨询有限公司",
        "unified_social_credit_code": "91330100MA2KABCD1A",
        "legal_representative": "王明",
        "registered_address": "杭州市西湖区文三路100号",
        "license_file_url": "mock://licenses/yichuang.pdf",
        "license_file_name": "营业执照.pdf",
    }


class TestCompanyCertifications:
    @pytest.mark.asyncio
    async def test_get_my_status_not_submitted(self, client: AsyncClient, test_recruiter_data):
        token = await register_and_get_token(client, test_recruiter_data)

        response = await client.get(
            "/api/v1/company-certifications/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_submitted"
        assert data["company_name"] is None

    @pytest.mark.asyncio
    async def test_recruiter_submit_certification(self, client: AsyncClient, test_recruiter_data):
        token = await register_and_get_token(client, test_recruiter_data)

        response = await client.post(
            "/api/v1/company-certifications/me",
            json=certification_payload(),
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["company_name"] == "杭州毅创越新信息咨询有限公司"
        assert data["unified_social_credit_code"] == "91330100MA2KABCD1A"
        assert data["verification_method"] == "business_license"

    @pytest.mark.asyncio
    async def test_recruiter_submit_enterprise_email_certification(self, client: AsyncClient, test_recruiter_data):
        token = await register_and_get_token(client, test_recruiter_data)

        response = await client.post(
            "/api/v1/company-certifications/me",
            json={
                "verification_method": "enterprise_email",
                "company_name": "杭州毅创越新信息咨询有限公司",
                "work_email": "hr@yichuang.example.com",
                "applicant_name": "李华",
                "applicant_title": "HRBP",
                "applicant_wechat": "hr_yichuang",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["verification_method"] == "enterprise_email"
        assert data["work_email"] == "hr@yichuang.example.com"
        assert data["applicant_wechat"] == "hr_yichuang"
        assert data["unified_social_credit_code"] is None

    @pytest.mark.asyncio
    async def test_hr_authorization_requires_proof_file(self, client: AsyncClient, test_recruiter_data):
        token = await register_and_get_token(client, test_recruiter_data)

        response = await client.post(
            "/api/v1/company-certifications/me",
            json={
                "verification_method": "hr_authorization",
                "company_name": "杭州毅创越新信息咨询有限公司",
                "applicant_name": "李华",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_recruiter_can_upload_license_for_ocr(self, client: AsyncClient, test_recruiter_data):
        token = await register_and_get_token(client, test_recruiter_data)

        response = await client.post(
            "/api/v1/company-certifications/license/ocr",
            files={"file": ("license_91330100MA2TEST607.png", b"fake image bytes", "image/png")},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["license_file_url"].startswith("/uploads/business_licenses/")
        assert data["license_file_name"] == "license_91330100MA2TEST607.png"
        assert data["unified_social_credit_code"] == "91330100MA2TEST607"
        assert data["company_name"]
        assert data["confidence"] > 0

    @pytest.mark.asyncio
    async def test_recruiter_can_upload_proof_file(self, client: AsyncClient, test_recruiter_data):
        token = await register_and_get_token(client, test_recruiter_data)

        response = await client.post(
            "/api/v1/company-certifications/proof-file",
            files={"file": ("authorization.pdf", b"fake pdf bytes", "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["proof_file_url"].startswith("/uploads/company_certification_proofs/")
        assert data["proof_file_name"] == "authorization.pdf"

    @pytest.mark.asyncio
    async def test_seeker_cannot_upload_license_for_ocr(self, client: AsyncClient, test_user_data):
        token = await register_and_get_token(client, test_user_data)

        response = await client.post(
            "/api/v1/company-certifications/license/ocr",
            files={"file": ("license.png", b"fake image bytes", "image/png")},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_license_ocr_rejects_unsupported_file(self, client: AsyncClient, test_recruiter_data):
        token = await register_and_get_token(client, test_recruiter_data)

        response = await client.post(
            "/api/v1/company-certifications/license/ocr",
            files={"file": ("license.txt", b"not a license", "text/plain")},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_seeker_cannot_submit_certification(self, client: AsyncClient, test_user_data):
        token = await register_and_get_token(client, test_user_data)

        response = await client.post(
            "/api/v1/company-certifications/me",
            json=certification_payload(),
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_list_and_approve(self, client: AsyncClient, test_recruiter_data, db_session):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        submit_response = await client.post(
            "/api/v1/company-certifications/me",
            json=certification_payload(),
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        certification_id = submit_response.json()["id"]

        admin_token = await create_admin_token(client, db_session)
        list_response = await client.get(
            "/api/v1/company-certifications/admin",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert list_response.status_code == 200
        assert list_response.json()["total"] == 1

        review_response = await client.post(
            f"/api/v1/company-certifications/admin/{certification_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert review_response.status_code == 200
        assert review_response.json()["status"] == "approved"

    @pytest.mark.asyncio
    async def test_seeker_can_view_public_approved_company(self, client: AsyncClient, test_recruiter_data, test_user_data, db_session):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        submit_response = await client.post(
            "/api/v1/company-certifications/me",
            json=certification_payload(),
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        certification = submit_response.json()
        admin_token = await create_admin_token(client, db_session)
        await client.post(
            f"/api/v1/company-certifications/admin/{certification['id']}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        seeker_token = await register_and_get_token(client, test_user_data)

        response = await client.get(
            f"/api/v1/company-certifications/public/recruiters/{certification['recruiter_id']}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "approved"
        assert response.json()["company_name"] == certification_payload()["company_name"]

    @pytest.mark.asyncio
    async def test_seeker_cannot_view_pending_company_publicly(self, client: AsyncClient, test_recruiter_data, test_user_data):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        submit_response = await client.post(
            "/api/v1/company-certifications/me",
            json=certification_payload(),
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        seeker_token = await register_and_get_token(client, test_user_data)

        response = await client.get(
            f"/api/v1/company-certifications/public/recruiters/{submit_response.json()['recruiter_id']}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_reject_requires_reason(self, client: AsyncClient, test_recruiter_data, db_session):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        submit_response = await client.post(
            "/api/v1/company-certifications/me",
            json=certification_payload(),
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        certification_id = submit_response.json()["id"]
        admin_token = await create_admin_token(client, db_session)

        response = await client.post(
            f"/api/v1/company-certifications/admin/{certification_id}/review",
            json={"action": "reject"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "驳回认证时必须填写原因" in response.json()["detail"]
