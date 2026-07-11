"""
Resume service tests.
"""

from types import SimpleNamespace

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

    def test_parse_text_to_structured_json_extracts_compact_chinese_basic_fields(self):
        structured, confidence = ResumeService._parse_text_to_structured_json(
            "\n".join(
                [
                    "个人简历",
                    "韩雨夏",
                    "女 27岁 本科 5年经验",
                    "职业方向：PeopleSoft 技术顾问",
                    "技能：PeopleSoft SQL",
                ]
            ),
            SimpleNamespace(display_name="测试用户"),
        )

        basic = structured["basic"]
        assert basic["name"] == "韩雨夏"
        assert basic["gender"] == "女"
        assert basic["age"] == 27
        assert basic["highest_education"] == "本科"
        assert basic["work_years"] == 5
        assert basic["target_position"] == "PeopleSoft 技术顾问"
        assert confidence > 0.5

    def test_parse_text_to_structured_json_uses_file_name_and_headline_fallbacks(self):
        structured, _ = ResumeService._parse_text_to_structured_json(
            "\n".join(
                [
                    "ii fb 31岁 丨 高级产品经理丨 7年经验 丨 本科 丨 在职",
                    "191-2042-7536 丨 hanyuxia185@163.com",
                    "个人总结",
                    "工作背景：拥有6年B端HR产品经验。",
                ]
            ),
            SimpleNamespace(display_name="测试用户"),
            original_name="HR高级产品经理 韩雨夏.pdf",
        )

        basic = structured["basic"]
        assert basic["name"] == "韩雨夏"
        assert basic["age"] == 31
        assert basic["highest_education"] == "本科"
        assert basic["work_years"] == 7
        assert basic["target_position"] == "高级产品经理"
