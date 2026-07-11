"""
Base data API tests.
"""
import pytest
from httpx import AsyncClient

from tests.test_api.test_company_certifications import create_admin_token, register_and_get_token


class TestBaseData:
    @pytest.mark.asyncio
    async def test_any_user_can_list_active_standard_positions_for_business_use(
        self,
        client: AsyncClient,
        db_session,
        test_recruiter_data,
    ):
        admin_token = await create_admin_token(client, db_session)
        headers = {"Authorization": f"Bearer {admin_token}"}
        await client.post(
            "/api/v1/base-data/standard-positions",
            json={"name": "前端开发工程师", "category": "技术研发", "aliases": ["前端工程师"]},
            headers=headers,
        )
        inactive_response = await client.post(
            "/api/v1/base-data/standard-positions",
            json={"name": "已停用职位", "category": "技术研发", "status": "inactive"},
            headers=headers,
        )
        assert inactive_response.status_code == 201

        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        response = await client.get(
            "/api/v1/base-data/standard-positions/public",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "前端开发工程师"
        assert data["items"][0]["status"] == "active"

    @pytest.mark.asyncio
    async def test_only_admin_can_manage_standard_positions(self, client: AsyncClient, test_user_data):
        seeker_token = await register_and_get_token(client, test_user_data)

        response = await client.get(
            "/api/v1/base-data/standard-positions",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_any_user_can_list_active_tags_for_business_use(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
    ):
        admin_token = await create_admin_token(client, db_session)
        headers = {"Authorization": f"Bearer {admin_token}"}
        active_response = await client.post(
            "/api/v1/base-data/tags",
            json={"name": "React", "category": "技能", "color": "#61dafb"},
            headers=headers,
        )
        inactive_response = await client.post(
            "/api/v1/base-data/tags",
            json={"name": "已停用标签", "category": "技能", "status": "inactive"},
            headers=headers,
        )
        assert active_response.status_code == 201
        assert inactive_response.status_code == 201

        seeker_token = await register_and_get_token(client, test_user_data)
        response = await client.get(
            "/api/v1/base-data/tags/public",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "React"
        assert data["items"][0]["status"] == "active"

    @pytest.mark.asyncio
    async def test_admin_can_create_list_update_and_deactivate_standard_position(
        self,
        client: AsyncClient,
        db_session,
    ):
        admin_token = await create_admin_token(client, db_session)
        headers = {"Authorization": f"Bearer {admin_token}"}

        create_response = await client.post(
            "/api/v1/base-data/standard-positions",
            json={
                "name": "后端工程师",
                "category": "技术研发",
                "aliases": ["后端开发", "服务端工程师", "后端开发"],
                "description": "负责服务端业务系统设计与开发",
            },
            headers=headers,
        )

        assert create_response.status_code == 201
        created = create_response.json()
        assert created["name"] == "后端工程师"
        assert created["aliases"] == ["后端开发", "服务端工程师"]
        assert created["status"] == "active"

        list_response = await client.get(
            "/api/v1/base-data/standard-positions",
            params={"q": "后端"},
            headers=headers,
        )

        assert list_response.status_code == 200
        listed = list_response.json()
        assert listed["total"] == 1
        assert listed["items"][0]["id"] == created["id"]

        update_response = await client.put(
            f"/api/v1/base-data/standard-positions/{created['id']}",
            json={
                "category": "互联网技术",
                "aliases": ["后端研发", "服务端研发"],
            },
            headers=headers,
        )

        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["category"] == "互联网技术"
        assert updated["aliases"] == ["后端研发", "服务端研发"]

        deactivate_response = await client.put(
            f"/api/v1/base-data/standard-positions/{created['id']}",
            json={"status": "inactive"},
            headers=headers,
        )

        assert deactivate_response.status_code == 200
        assert deactivate_response.json()["status"] == "inactive"

        logs_response = await client.get(
            "/api/v1/base-data/operation-logs",
            params={"resource_type": "standard_position", "resource_id": created["id"], "limit": 10},
            headers=headers,
        )

        assert logs_response.status_code == 200
        logs = logs_response.json()
        assert logs["total"] == 3
        assert {item["action"] for item in logs["items"]} == {"create", "update", "deactivate"}

    @pytest.mark.asyncio
    async def test_admin_can_get_standard_position_detail(self, client: AsyncClient, db_session):
        admin_token = await create_admin_token(client, db_session)
        headers = {"Authorization": f"Bearer {admin_token}"}
        create_response = await client.post(
            "/api/v1/base-data/standard-positions",
            json={
                "name": "数据分析师",
                "category": "数据",
                "aliases": ["BI 分析师", "商业分析师"],
                "description": "负责业务指标分析与数据洞察",
            },
            headers=headers,
        )
        created = create_response.json()

        response = await client.get(
            f"/api/v1/base-data/standard-positions/{created['id']}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created["id"]
        assert data["name"] == "数据分析师"
        assert data["category"] == "数据"
        assert data["aliases"] == ["BI 分析师", "商业分析师"]
        assert data["description"] == "负责业务指标分析与数据洞察"
        assert data["created_by"] is not None
        assert data["updated_by"] is not None

    @pytest.mark.asyncio
    async def test_standard_position_detail_returns_404_when_missing(self, client: AsyncClient, db_session):
        admin_token = await create_admin_token(client, db_session)

        response = await client.get(
            "/api/v1/base-data/standard-positions/999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Standard position not found"

    @pytest.mark.asyncio
    async def test_admin_cannot_create_duplicate_standard_position(self, client: AsyncClient, db_session):
        admin_token = await create_admin_token(client, db_session)
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {
            "name": "产品经理",
            "category": "产品",
            "aliases": ["PM"],
        }

        first_response = await client.post("/api/v1/base-data/standard-positions", json=payload, headers=headers)
        duplicate_response = await client.post("/api/v1/base-data/standard-positions", json=payload, headers=headers)

        assert first_response.status_code == 201
        assert duplicate_response.status_code == 409

    @pytest.mark.asyncio
    async def test_admin_can_manage_tag_library_with_hierarchy_and_logs(self, client: AsyncClient, db_session):
        admin_token = await create_admin_token(client, db_session)
        headers = {"Authorization": f"Bearer {admin_token}"}

        parent_response = await client.post(
            "/api/v1/base-data/tags",
            json={
                "name": "编程语言",
                "category": "skill",
                "color": "#2563eb",
                "sort_order": 1,
            },
            headers=headers,
        )
        assert parent_response.status_code == 201
        parent = parent_response.json()

        child_response = await client.post(
            "/api/v1/base-data/tags",
            json={
                "name": "Python",
                "category": "skill",
                "parent_id": parent["id"],
                "color": "#16a34a",
                "description": "后端与数据分析常用技能",
                "sort_order": 10,
            },
            headers=headers,
        )
        assert child_response.status_code == 201
        child = child_response.json()
        assert child["parent_id"] == parent["id"]
        assert child["status"] == "active"

        list_response = await client.get(
            "/api/v1/base-data/tags",
            params={"category": "skill"},
            headers=headers,
        )
        assert list_response.status_code == 200
        listed = list_response.json()
        assert listed["total"] == 2

        update_response = await client.put(
            f"/api/v1/base-data/tags/{child['id']}",
            json={"name": "Python 3", "sort_order": 20},
            headers=headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Python 3"
        assert update_response.json()["sort_order"] == 20

        deactivate_response = await client.put(
            f"/api/v1/base-data/tags/{child['id']}",
            json={"status": "inactive"},
            headers=headers,
        )
        assert deactivate_response.status_code == 200
        assert deactivate_response.json()["status"] == "inactive"

        logs_response = await client.get(
            "/api/v1/base-data/operation-logs",
            params={"resource_type": "tag", "resource_id": child["id"], "limit": 10},
            headers=headers,
        )
        assert logs_response.status_code == 200
        logs = logs_response.json()
        assert logs["total"] == 3
        assert {item["action"] for item in logs["items"]} == {"create", "update", "deactivate"}

    @pytest.mark.asyncio
    async def test_admin_can_get_tag_library_detail(self, client: AsyncClient, db_session):
        admin_token = await create_admin_token(client, db_session)
        headers = {"Authorization": f"Bearer {admin_token}"}
        parent_response = await client.post(
            "/api/v1/base-data/tags",
            json={"name": "数据能力", "category": "skill", "color": "#2563eb"},
            headers=headers,
        )
        parent = parent_response.json()
        child_response = await client.post(
            "/api/v1/base-data/tags",
            json={
                "name": "SQL",
                "category": "skill",
                "parent_id": parent["id"],
                "color": "#16a34a",
                "description": "结构化查询与数据处理",
                "sort_order": 12,
            },
            headers=headers,
        )
        child = child_response.json()

        response = await client.get(
            f"/api/v1/base-data/tags/{child['id']}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == child["id"]
        assert data["name"] == "SQL"
        assert data["category"] == "skill"
        assert data["parent_id"] == parent["id"]
        assert data["color"] == "#16a34a"
        assert data["description"] == "结构化查询与数据处理"
        assert data["sort_order"] == 12
        assert data["created_by"] is not None
        assert data["updated_by"] is not None

    @pytest.mark.asyncio
    async def test_tag_library_detail_returns_404_when_missing(self, client: AsyncClient, db_session):
        admin_token = await create_admin_token(client, db_session)

        response = await client.get(
            "/api/v1/base-data/tags/999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Tag not found"

    @pytest.mark.asyncio
    async def test_tag_library_rejects_duplicate_and_invalid_parent(self, client: AsyncClient, db_session):
        admin_token = await create_admin_token(client, db_session)
        headers = {"Authorization": f"Bearer {admin_token}"}

        payload = {"name": "制造业", "category": "industry"}
        first_response = await client.post("/api/v1/base-data/tags", json=payload, headers=headers)
        duplicate_response = await client.post("/api/v1/base-data/tags", json=payload, headers=headers)
        invalid_parent_response = await client.post(
            "/api/v1/base-data/tags",
            json={"name": "不存在父级", "category": "industry", "parent_id": 999999},
            headers=headers,
        )
        self_parent_response = await client.put(
            f"/api/v1/base-data/tags/{first_response.json()['id']}",
            json={"parent_id": first_response.json()["id"]},
            headers=headers,
        )

        assert first_response.status_code == 201
        assert duplicate_response.status_code == 409
        assert invalid_parent_response.status_code == 404
        assert self_parent_response.status_code == 422

    @pytest.mark.asyncio
    async def test_only_admin_can_manage_tag_library(self, client: AsyncClient, test_user_data):
        seeker_token = await register_and_get_token(client, test_user_data)

        response = await client.get(
            "/api/v1/base-data/tags",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 403
