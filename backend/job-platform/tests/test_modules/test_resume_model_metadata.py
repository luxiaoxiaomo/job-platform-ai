"""Resume model metadata registration tests."""

from app.db.base import Base
from app.modules.resume.models import ResumeParseRun  # noqa: F401


def test_resume_parse_run_foreign_key_targets_are_registered():
    """Importing resume models should register tables needed by its foreign keys."""

    assert "resume_parse_runs" in Base.metadata.tables
    assert "users" in Base.metadata.tables
    assert "ai_prompt_configs" in Base.metadata.tables
