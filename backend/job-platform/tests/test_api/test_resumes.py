"""
Resume API tests.
"""
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from httpx import AsyncClient

from tests.test_api.test_company_certifications import create_admin_token


def _build_docx_bytes(text: str) -> bytes:
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>{text}</w:t></w:r></w:p>
  </w:body>
</w:document>"""
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
        archive.writestr("word/document.xml", document_xml)
    return buffer.getvalue()


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_pdf_bytes(text: str) -> bytes:
    text_parts = []
    for index, line in enumerate(text.splitlines() or [""]):
        if index:
            text_parts.append("T*")
        text_parts.append(f"({_pdf_escape(line)}) Tj")
    stream = f"BT /F1 12 Tf 14 TL 72 720 Td {' '.join(text_parts)} ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


async def _register_seeker(client: AsyncClient, user_data: dict) -> str:
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


class TestResumes:
    """Resume upload API behavior."""

    @pytest.mark.asyncio
    async def test_profile_summary_empty_state(self, client: AsyncClient, test_user_data):
        token = await _register_seeker(client, test_user_data)

        response = await client.get(
            "/api/v1/resumes/me/profile-summary",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        summary = response.json()
        assert summary["resume"] is None
        assert summary["profile"] is None
        assert summary["basic_info"] is None
        assert summary["summaries"] == {
            "educations": [],
            "work_experiences": [],
            "projects": [],
            "skills": [],
            "certificates": [],
        }
        assert summary["completeness"]["core"] == {
            "score": 0,
            "filled_count": 0,
            "total_count": 0,
            "missing_fields": [],
        }
        assert summary["completeness"]["recommended"]["total_count"] == 0
        assert summary["review"] == {
            "needs_review": False,
            "unconfirmed_count": 0,
            "low_confidence_count": 0,
            "status_label": "未上传",
        }
        assert summary["source_links"]["parse_run_id"] is None

    @pytest.mark.asyncio
    async def test_upload_docx_creates_upload_and_parse_run(self, client: AsyncClient, test_user_data):
        token = await _register_seeker(client, test_user_data)
        content = _build_docx_bytes("姓名：孙明明\n年龄：28\n性别：男\n目标岗位：PeopleSoft 技术顾问\n工作经验：12年\n项目 技能 教育")

        response = await client.post(
            "/api/v1/resumes/me/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={
                "file": (
                "孙明明简历.docx",
                    content,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"resume", "upload", "parse_run"}
        assert data["resume"]["parsed_snapshot"].startswith("简历文件 | 孙明明简历.docx")
        assert data["resume"]["current_upload_id"] == data["upload"]["id"]
        assert data["resume"]["current_parse_run_id"] == data["parse_run"]["id"]
        assert data["upload"]["status"] == "parsed"
        assert data["parse_run"]["status"] == "succeeded"
        assert data["parse_run"]["extractor"] == "docx"
        assert data["parse_run"]["metrics_json"]["chunk_count"] >= 1

        status_response = await client.get(
            "/api/v1/resumes/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["has_resume"] is True
        assert status_data["latest_upload"]["id"] == data["upload"]["id"]
        assert status_data["latest_parse_run"]["id"] == data["parse_run"]["id"]

        history_response = await client.get(
            "/api/v1/resumes/me/uploads",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert history_response.status_code == 200
        history_data = history_response.json()
        assert len(history_data) == 1
        assert history_data[0]["upload"]["id"] == data["upload"]["id"]
        assert history_data[0]["latest_parse_run"]["id"] == data["parse_run"]["id"]

        detail_response = await client.get(
            f"/api/v1/resumes/me/parse-runs/{data['parse_run']['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert detail_data["upload"]["id"] == data["upload"]["id"]
        assert detail_data["parse_run"]["id"] == data["parse_run"]["id"]
        assert "PeopleSoft" in detail_data["extracted_text"]["text_preview"]
        assert detail_data["extracted_text"]["char_count"] > 0
        assert len(detail_data["chunks"]) >= 1
        assert "PeopleSoft" in detail_data["chunks"][0]["content_preview"]

        auto_structured_response = await client.get(
            f"/api/v1/resumes/me/parse-runs/{data['parse_run']['id']}/structured",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert auto_structured_response.status_code == 200
        auto_structured = auto_structured_response.json()
        assert auto_structured["profile"]["source"] == "rule"
        assert auto_structured["profile"]["status"] == "validated"
        assert auto_structured["basic_info"]["real_name"] == "孙明明"
        assert auto_structured["basic_info"]["age"] == 28
        assert auto_structured["basic_info"]["gender"] == "男"
        assert auto_structured["basic_info"]["target_position"] == "PeopleSoft 技术顾问"

        summary_response = await client.get(
            "/api/v1/resumes/me/profile-summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert summary_response.status_code == 200
        summary = summary_response.json()
        assert summary["resume"]["current_parse_run_id"] == data["parse_run"]["id"]
        assert summary["profile"]["id"] == auto_structured["profile"]["id"]
        assert summary["basic_info"]["real_name"] == "孙明明"
        assert summary["basic_info"]["age"] == 28
        assert summary["completeness"]["core"]["total_count"] == 5
        assert summary["completeness"]["recommended"]["total_count"] == 9
        assert "手机号" in summary["completeness"]["recommended"]["missing_fields"]
        assert "手机号" not in summary["completeness"]["core"]["missing_fields"]
        assert summary["review"]["needs_review"] is True
        assert summary["review"]["unconfirmed_count"] == 1
        assert summary["review"]["status_label"] == "待确认"
        assert summary["source_links"]["parse_run_id"] == data["parse_run"]["id"]
        assert summary["source_links"]["structured_url"].endswith(f"/{data['parse_run']['id']}/structured")
        assert summary["source_links"]["confirm_page_path"].endswith(str(data["parse_run"]["id"]))

        profile_response = await client.get(
            "/api/v1/seeker-profiles/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile_response.status_code == 200
        assert profile_response.json()["real_name"] is None

        other_user_data = {
            **test_user_data,
            "phone": "13800138001",
            "display_name": "Other Seeker",
        }
        other_token = await _register_seeker(client, other_user_data)
        forbidden_response = await client.get(
            f"/api/v1/resumes/me/parse-runs/{data['parse_run']['id']}",
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert forbidden_response.status_code == 404

    @pytest.mark.asyncio
    async def test_failed_upload_does_not_replace_current_successful_parse_run(self, client: AsyncClient, test_user_data):
        token = await _register_seeker(client, test_user_data)
        docx_content = _build_docx_bytes("姓名：孙明明\n年龄：28\n性别：男\n目标岗位：PeopleSoft 技术顾问")

        success_response = await client.post(
            "/api/v1/resumes/me/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={
                "file": (
                    "孙明明简历.docx",
                    docx_content,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        assert success_response.status_code == 200
        success_data = success_response.json()
        current_parse_run_id = success_data["parse_run"]["id"]

        failed_response = await client.post(
            "/api/v1/resumes/me/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("broken.png", b"not-an-image", "image/png")},
        )

        assert failed_response.status_code == 200
        failed_data = failed_response.json()
        assert failed_data["upload"]["status"] == "failed"
        assert failed_data["parse_run"]["status"] == "completed_with_errors"
        assert failed_data["resume"]["current_parse_run_id"] == current_parse_run_id

        summary_response = await client.get(
            "/api/v1/resumes/me/profile-summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert summary_response.status_code == 200
        summary = summary_response.json()
        assert summary["source_links"]["parse_run_id"] == current_parse_run_id
        assert summary["basic_info"]["real_name"] == "孙明明"

    @pytest.mark.asyncio
    async def test_upload_pdf_extracts_text_and_creates_parse_run(self, client: AsyncClient, test_user_data):
        token = await _register_seeker(client, test_user_data)
        content = _build_pdf_bytes(
            "\n".join(
                [
                    "Name: Han Yuxia",
                    "Gender: Female",
                    "Age: 27",
                    "Highest Education: Bachelor",
                    "Work Experience: 5 years",
                    "Target Position: PeopleSoft Consultant",
                    "Skills: PeopleSoft SQL",
                ]
            )
        )

        response = await client.post(
            "/api/v1/resumes/me/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("han-yuxia-resume.pdf", content, "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["upload"]["status"] == "parsed"
        assert data["parse_run"]["status"] == "succeeded"
        assert data["parse_run"]["extractor"] == "pdf_text"

        detail_response = await client.get(
            f"/api/v1/resumes/me/parse-runs/{data['parse_run']['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert "Han Yuxia" in detail_data["extracted_text"]["text_preview"]
        assert detail_data["extracted_text"]["char_count"] > 0
        assert len(detail_data["chunks"]) >= 1
        assert "PeopleSoft" in detail_data["chunks"][0]["content_preview"]

        auto_structured_response = await client.get(
            f"/api/v1/resumes/me/parse-runs/{data['parse_run']['id']}/structured",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert auto_structured_response.status_code == 200
        auto_structured = auto_structured_response.json()
        assert auto_structured["basic_info"]["real_name"] == "Han Yuxia"
        assert auto_structured["basic_info"]["age"] == 27
        assert auto_structured["basic_info"]["gender"] == "女"
        assert auto_structured["basic_info"]["highest_education"] == "本科"
        assert auto_structured["basic_info"]["work_years"] == 5
        assert auto_structured["basic_info"]["target_position"] == "PeopleSoft Consultant"

    @pytest.mark.asyncio
    async def test_structured_profile_can_project_to_detail_tables(self, client: AsyncClient, test_user_data):
        token = await _register_seeker(client, test_user_data)
        content = _build_docx_bytes("王明雷 PeopleSoft 技术顾问 12年经验 项目 技能 教育")

        upload_response = await client.post(
            "/api/v1/resumes/me/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={
                "file": (
                    "resume.docx",
                    content,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        assert upload_response.status_code == 200
        parse_run_id = upload_response.json()["parse_run"]["id"]

        structured_json = {
            "basic": {
                "name": "王明雷",
                "gender": "男",
                "highest_education": "硕士",
                "work_years": 12,
                "target_position": "PeopleSoft 技术顾问",
                "confidence_score": 0.92,
            },
            "education": [
                {
                    "school_name": "上海交通大学",
                    "major": "软件工程",
                    "degree": "硕士",
                    "start_date": "2024",
                    "end_date": "2026",
                    "confidence_score": 0.86,
                }
            ],
            "work_experiences": [
                {
                    "company_name": "汉得信息",
                    "position": "技术顾问",
                    "description": "负责人事薪酬系统实施和优化",
                    "confidence_score": 0.88,
                }
            ],
            "projects": [
                {
                    "project_name": "得物 PeopleSoft HCM 项目",
                    "role": "技术顾问",
                    "responsibility": "需求分析、二开和上线支持",
                    "confidence_score": 0.83,
                }
            ],
            "skills": [
                {"skill_name": "PeopleSoft", "skill_level": "熟练", "category": "ERP", "confidence_score": 0.95},
                {"skill_name": "HCM", "category": "业务系统", "confidence_score": 0.91},
            ],
            "certificates": [
                {"certificate_name": "PMP", "certificate_type": "项目管理", "confidence_score": 0.8}
            ],
        }
        create_response = await client.post(
            "/api/v1/resumes/me/structured-profiles",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "parse_run_id": parse_run_id,
                "source": "manual",
                "status": "needs_review",
                "confidence_score": 0.9,
                "structured_json": structured_json,
            },
        )

        assert create_response.status_code == 200
        profile = create_response.json()
        assert profile["parse_run_id"] == parse_run_id
        assert profile["status"] == "needs_review"
        assert profile["structured_json"]["basic"]["name"] == "王明雷"

        parse_run_structured_response = await client.get(
            f"/api/v1/resumes/me/parse-runs/{parse_run_id}/structured",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert parse_run_structured_response.status_code == 200
        parse_run_structured = parse_run_structured_response.json()
        assert parse_run_structured["profile"]["id"] == profile["id"]
        assert parse_run_structured["profile"]["structured_json"]["basic"]["name"] == "王明雷"

        project_response = await client.post(
            f"/api/v1/resumes/me/structured-profiles/{profile['id']}/project",
            headers={"Authorization": f"Bearer {token}"},
            json={"confirm": True, "min_confidence": 0.8},
        )

        assert project_response.status_code == 200
        projected = project_response.json()
        assert projected["profile"]["status"] == "confirmed"
        assert projected["projected_counts"] == {
            "basic_info": 1,
            "educations": 1,
            "work_experiences": 1,
            "projects": 1,
            "skills": 2,
            "certificates": 1,
        }
        assert projected["detail"]["basic_info"]["real_name"] == "王明雷"
        assert projected["detail"]["educations"][0]["school_name"] == "上海交通大学"
        assert projected["detail"]["skills"][0]["skill_name"] == "PeopleSoft"

        latest_response = await client.get(
            "/api/v1/resumes/me/structured-profiles/latest",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert latest_response.status_code == 200
        latest = latest_response.json()
        assert latest["profile"]["id"] == profile["id"]
        assert latest["basic_info"]["target_position"] == "PeopleSoft 技术顾问"

        confirm_response = await client.put(
            "/api/v1/resumes/me/structured/confirm",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "parse_run_id": parse_run_id,
                "min_confidence": 0.85,
                "structured_json": {
                    **structured_json,
                    "basic": {
                        **structured_json["basic"],
                        "target_position": "PeopleSoft HCM 顾问",
                    },
                },
            },
        )
        assert confirm_response.status_code == 200
        confirmed = confirm_response.json()
        assert confirmed["profile"]["status"] == "confirmed"
        assert confirmed["detail"]["basic_info"]["target_position"] == "PeopleSoft HCM 顾问"

        post_confirm_response = await client.post(
            "/api/v1/resumes/me/structured/confirm",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "parse_run_id": parse_run_id,
                "min_confidence": 0.85,
                "structured_json": {
                    **structured_json,
                    "basic": {
                        **structured_json["basic"],
                        "target_position": "PeopleSoft HCM 顾问",
                    },
                },
            },
        )
        assert post_confirm_response.status_code == 200
        assert post_confirm_response.json()["profile"]["status"] == "confirmed"

        summary_response = await client.get(
            "/api/v1/resumes/me/profile-summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert summary_response.status_code == 200
        summary = summary_response.json()
        assert summary["profile"]["id"] == profile["id"]
        assert summary["basic_info"]["target_position"] == "PeopleSoft HCM 顾问"
        assert summary["summaries"]["skills"][0]["skill_name"] == "PeopleSoft"
        assert summary["completeness"]["core"]["total_count"] == 5
        assert summary["completeness"]["core"]["missing_fields"] == []
        assert summary["completeness"]["recommended"]["total_count"] == 9
        assert summary["review"]["needs_review"] is False
        assert summary["review"]["unconfirmed_count"] == 0
        assert summary["review"]["status_label"] == "已确认"
        assert summary["source_links"]["parse_run_id"] == parse_run_id

        synced_profile_response = await client.get(
            "/api/v1/seeker-profiles/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert synced_profile_response.status_code == 200
        synced_profile = synced_profile_response.json()
        assert synced_profile["real_name"] == "王明雷"
        assert synced_profile["gender"] == "男"
        assert synced_profile["target_position"] == "PeopleSoft HCM 顾问"

        other_user_data = {
            **test_user_data,
            "phone": "13800138002",
            "display_name": "Other Seeker",
        }
        other_token = await _register_seeker(client, other_user_data)
        forbidden_response = await client.get(
            f"/api/v1/resumes/me/structured-profiles/{profile['id']}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert forbidden_response.status_code == 404

    @pytest.mark.asyncio
    async def test_structured_profile_can_link_tag_library_items(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
    ):
        admin_token = await create_admin_token(client, db_session)
        tag_response = await client.post(
            "/api/v1/base-data/tags",
            json={"name": "PeopleSoft", "category": "技能", "color": "#1f7ae0"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        tag = tag_response.json()
        token = await _register_seeker(client, test_user_data)
        upload_response = await client.post(
            "/api/v1/resumes/me/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={
                "file": (
                    "resume.docx",
                    _build_docx_bytes("PeopleSoft SQL HCM"),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        parse_run_id = upload_response.json()["parse_run"]["id"]

        create_response = await client.post(
            "/api/v1/resumes/me/structured-profiles",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "parse_run_id": parse_run_id,
                "structured_json": {"basic": {"name": "王明雷"}, "skills": [{"skill_name": "PeopleSoft"}]},
                "tag_ids": [tag["id"]],
            },
        )

        assert create_response.status_code == 200
        profile = create_response.json()
        assert profile["tag_refs"] == [
            {"id": tag["id"], "name": "PeopleSoft", "category": "技能", "color": "#1f7ae0"}
        ]

        latest_response = await client.get(
            "/api/v1/resumes/me/structured-profiles/latest",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert latest_response.status_code == 200
        assert latest_response.json()["profile"]["tag_refs"][0]["id"] == tag["id"]

        confirm_response = await client.put(
            "/api/v1/resumes/me/structured/confirm",
            headers={"Authorization": f"Bearer {token}"},
            json={"parse_run_id": parse_run_id, "tag_ids": [tag["id"]]},
        )
        assert confirm_response.status_code == 200
        assert confirm_response.json()["profile"]["tag_refs"][0]["name"] == "PeopleSoft"

    @pytest.mark.asyncio
    async def test_structured_profile_rejects_missing_tag_library_item(
        self,
        client: AsyncClient,
        test_user_data,
    ):
        token = await _register_seeker(client, test_user_data)
        upload_response = await client.post(
            "/api/v1/resumes/me/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={
                "file": (
                    "resume.docx",
                    _build_docx_bytes("PeopleSoft SQL HCM"),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        parse_run_id = upload_response.json()["parse_run"]["id"]

        response = await client.post(
            "/api/v1/resumes/me/structured-profiles",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "parse_run_id": parse_run_id,
                "structured_json": {"basic": {"name": "王明雷"}},
                "tag_ids": [999999],
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Tag not found"
