"""
Resume service tests.
"""

from app.modules.resume.service import ResumeService


class TestResumeService:
    """Resume service behavior."""

    def test_build_snapshot_uses_readable_chinese_text(self):
        """Uploaded resume snapshots should not contain mojibake text."""
        snapshot = ResumeService._build_snapshot(
            current_user=None,
            original_name="王明雷简历.docx",
            file_size=36212,
        )

        assert snapshot == (
            "简历文件 | 王明雷简历.docx | 35KB | "
            "已上传简历文件，当前生成规则快照；后续可接入 AI 精细解析。"
        )
        assert "绠" not in snapshot
        assert "宸" not in snapshot
