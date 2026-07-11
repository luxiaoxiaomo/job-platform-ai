"""Regression tests for the repository consistency gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
CHECK_SCRIPT = PROJECT_ROOT / "scripts" / "check_project_consistency.py"


def run_consistency_check(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK_SCRIPT), "--root", str(root)],
        capture_output=True,
        check=False,
        text=True,
    )


def test_repository_active_ports_are_consistent() -> None:
    result = run_consistency_check(PROJECT_ROOT)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Project consistency checks passed" in result.stdout


def test_check_reports_an_incorrect_backend_entrypoint_port(tmp_path: Path) -> None:
    files = {
        "frontend/wechat-prototype/package.json": """
            {"scripts":{"dev":"vite --host 127.0.0.1 --port 5174 --strictPort"}}
        """,
        "frontend/wechat-prototype/src/services/api.js": (
            "const url = 'http://127.0.0.1:8003'\n"
        ),
        "frontend/wechat-prototype/启动前端.bat": (
            "echo URL: http://localhost:5174\n"
            "echo API: http://localhost:8003\n"
        ),
        "backend/job-platform/test_api.ps1": (
            "Write-Host 'Port 8003'\n"
            '$BASE_URL = "http://127.0.0.1:8003"\n'
        ),
        "backend/job-platform/app/main.py": (
            "import uvicorn\n"
            "uvicorn.run('app.main:app', port=8000)\n"
        ),
        "README.md": (
            "poetry run uvicorn app.main:app --port 8003\n"
            "http://localhost:5174\n"
        ),
        "backend/job-platform/README.md": (
            "poetry run uvicorn app.main:app --port 8003\n"
        ),
    }
    for relative_path, content in files.items():
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    result = run_consistency_check(tmp_path)

    assert result.returncode == 1
    assert "backend entrypoint must run on port 8003" in result.stdout
