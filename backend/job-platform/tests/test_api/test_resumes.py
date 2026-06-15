"""
Resume API tests.
"""
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from httpx import AsyncClient


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
    async def test_upload_docx_creates_upload_and_parse_run(self, client: AsyncClient, test_user_data):
        token = await _register_seeker(client, test_user_data)
        content = _build_docx_bytes("王明雷 PeopleSoft 技术顾问 12年经验 项目 技能 教育")

        response = await client.post(
            "/api/v1/resumes/me/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={
                "file": (
                    "王明雷简历.docx",
                    content,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"resume", "upload", "parse_run"}
        assert data["resume"]["parsed_snapshot"].startswith("简历文件 | 王明雷简历.docx")
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
