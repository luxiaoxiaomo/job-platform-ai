"""
用户API测试
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select


class TestUsers:
    """用户API测试类"""

    async def _register_and_login(self, client: AsyncClient, user_data: dict) -> str:
        """辅助方法：注册并登录，返回Token"""
        # 获取验证码
        code_response = await client.post(
            "/api/v1/auth/send-verification-code",
            params={"phone": user_data["phone"]}
        )
        code = code_response.json()["code"]

        # 注册
        register_data = {**user_data, "verification_code": code}
        register_response = await client.post(
            "/api/v1/auth/register",
            json=register_data
        )

        return register_response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_get_current_user_info(self, client: AsyncClient, test_user_data):
        """测试获取当前用户信息"""
        # 注册并登录
        token = await self._register_and_login(client, test_user_data)

        # 获取当前用户信息
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == test_user_data["phone"]
        assert data["display_name"] == test_user_data["display_name"]
        assert data["role"] == test_user_data["role"]

    @pytest.mark.asyncio
    async def test_get_current_user_without_token(self, client: AsyncClient):
        """测试获取当前用户信息 - 未登录"""
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401  # 401 Unauthorized（缺少token）

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """测试获取当前用户信息 - Token无效"""
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_current_user(self, client: AsyncClient, test_user_data):
        """测试更新当前用户信息"""
        # 注册并登录
        token = await self._register_and_login(client, test_user_data)

        # 更新用户信息
        update_data = {
            "display_name": "新名称",
            "avatar_url": "https://example.com/avatar.jpg"
        }
        response = await client.put(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "新名称"
        assert data["avatar_url"] == update_data["avatar_url"]

    @pytest.mark.asyncio
    async def test_get_user_by_id_self(self, client: AsyncClient, test_user_data):
        """测试获取指定用户信息 - 访问自己"""
        # 注册并登录
        token = await self._register_and_login(client, test_user_data)

        # 先获取自己的ID
        me_response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        user_id = me_response.json()["id"]

        # 通过ID访问自己
        response = await client.get(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["id"] == user_id

    @pytest.mark.asyncio
    async def test_get_user_by_id_other_user_forbidden(
        self,
        client: AsyncClient,
        test_user_data,
        test_recruiter_data
    ):
        """测试获取指定用户信息 - 访问他人（应该被拒绝）"""
        # 注册两个用户
        token_user_a = await self._register_and_login(client, test_user_data)
        token_user_b = await self._register_and_login(client, test_recruiter_data)

        # 用户B获取自己的ID
        me_response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token_user_b}"}
        )
        user_b_id = me_response.json()["id"]

        # 用户A尝试访问用户B的信息（应该被拒绝）
        response = await client.get(
            f"/api/v1/users/{user_b_id}",
            headers={"Authorization": f"Bearer {token_user_a}"}
        )

        assert response.status_code == 403
        assert "无权访问" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_user_by_id_admin_can_access(
        self,
        client: AsyncClient,
        test_user_data,
        db_session
    ):
        """测试获取指定用户信息 - admin可以访问任何用户"""
        # 创建普通用户
        token_user = await self._register_and_login(client, test_user_data)
        me_response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token_user}"}
        )
        normal_user_id = me_response.json()["id"]

        # 手动创建admin用户
        from app.modules.user.models import User
        from app.core.security import hash_password
        from app.utils.encryption import encryptor
        from app.utils.phone_hash import hash_phone

        admin_phone = "13700137000"
        admin = User(
            phone_hash=hash_phone(admin_phone),
            phone_encrypted=encryptor.encrypt(admin_phone),
            password_hash=hash_password("Admin1234"),
            display_name="管理员",
            role="admin",
            status="active"
        )
        db_session.add(admin)
        await db_session.commit()

        # admin登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"phone": admin_phone, "password": "Admin1234"}
        )
        admin_token = login_response.json()["access_token"]

        # admin访问普通用户信息（应该成功）
        response = await client.get(
            f"/api/v1/users/{normal_user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        assert response.json()["id"] == normal_user_id

    @pytest.mark.asyncio
    async def test_admin_can_list_users(self, client: AsyncClient, test_user_data, test_recruiter_data, db_session):
        token_user = await self._register_and_login(client, test_user_data)
        await self._register_and_login(client, test_recruiter_data)

        from app.core.security import hash_password
        from app.modules.user.models import User
        from app.utils.encryption import encryptor
        from app.utils.phone_hash import hash_phone

        recruiter = (
            await db_session.execute(
                select(User).where(User.phone_hash == hash_phone(test_recruiter_data["phone"]))
            )
        ).scalar_one()
        recruiter.phone_encrypted = "ciphertext-from-an-old-key"
        await db_session.commit()

        admin_phone = "13700137001"
        admin = User(
            phone_hash=hash_phone(admin_phone),
            phone_encrypted=encryptor.encrypt(admin_phone),
            password_hash=hash_password("Admin1234"),
            display_name="管理员",
            role="admin",
            status="active",
        )
        db_session.add(admin)
        await db_session.commit()

        login_response = await client.post(
            "/api/v1/auth/login",
            json={"phone": admin_phone, "password": "Admin1234"},
        )
        admin_token = login_response.json()["access_token"]

        forbidden = await client.get(
            "/api/v1/users/admin",
            headers={"Authorization": f"Bearer {token_user}"},
        )
        response = await client.get(
            "/api/v1/users/admin",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        recruiter_response = await client.get(
            "/api/v1/users/admin",
            params={"role": "recruiter"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert forbidden.status_code == 403
        assert response.status_code == 200
        assert response.json()["total"] == 3
        assert {item["role"] for item in response.json()["items"]} == {"seeker", "recruiter", "admin"}
        assert recruiter_response.status_code == 200
        assert recruiter_response.json()["total"] == 1
        assert recruiter_response.json()["items"][0]["role"] == "recruiter"
        assert recruiter_response.json()["items"][0]["phone"] == "手机号不可用"
