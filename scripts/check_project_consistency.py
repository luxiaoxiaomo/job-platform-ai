"""Validate active local ports and build entry points used by CI."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path


FRONTEND_PORT = 5174
BACKEND_PORT = 8003


def _read_text(root: Path, relative_path: str, errors: list[str]) -> str:
    path = root / relative_path
    if not path.is_file():
        errors.append(f"missing required file: {relative_path}")
        return ""
    return path.read_text(encoding="utf-8")


def _require_text(
    root: Path,
    relative_path: str,
    required_text: str,
    message: str,
    errors: list[str],
) -> None:
    content = _read_text(root, relative_path, errors)
    if content and required_text not in content:
        errors.append(message)


def _backend_entrypoint_port(root: Path, errors: list[str]) -> int | None:
    relative_path = "backend/job-platform/app/main.py"
    content = _read_text(root, relative_path, errors)
    if not content:
        return None
    try:
        tree = ast.parse(content, filename=relative_path)
    except SyntaxError as exc:
        errors.append(f"cannot parse {relative_path}: {exc}")
        return None

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (
            isinstance(func, ast.Attribute)
            and func.attr == "run"
            and isinstance(func.value, ast.Name)
            and func.value.id == "uvicorn"
        ):
            continue
        for keyword in node.keywords:
            if keyword.arg == "port" and isinstance(keyword.value, ast.Constant):
                return keyword.value.value if isinstance(keyword.value.value, int) else None
    return None


def collect_consistency_errors(root: Path) -> list[str]:
    errors: list[str] = []

    package_path = "frontend/wechat-prototype/package.json"
    package_text = _read_text(root, package_path, errors)
    if package_text:
        try:
            package = json.loads(package_text)
        except json.JSONDecodeError as exc:
            errors.append(f"cannot parse {package_path}: {exc}")
        else:
            dev_script = str(package.get("scripts", {}).get("dev", ""))
            if f"--port {FRONTEND_PORT}" not in dev_script or "--strictPort" not in dev_script:
                errors.append(
                    f"frontend dev script must use strict port {FRONTEND_PORT}"
                )
            if not package.get("scripts", {}).get("build"):
                errors.append("frontend package must define a build script")

    _require_text(
        root,
        "frontend/wechat-prototype/src/services/api.js",
        f"http://127.0.0.1:{BACKEND_PORT}",
        f"frontend API fallback must target backend port {BACKEND_PORT}",
        errors,
    )
    _require_text(
        root,
        "frontend/wechat-prototype/启动前端.bat",
        f"http://localhost:{FRONTEND_PORT}",
        f"frontend launcher must advertise port {FRONTEND_PORT}",
        errors,
    )
    _require_text(
        root,
        "frontend/wechat-prototype/启动前端.bat",
        f"http://localhost:{BACKEND_PORT}",
        f"frontend launcher must advertise backend port {BACKEND_PORT}",
        errors,
    )
    _require_text(
        root,
        "backend/job-platform/test_api.ps1",
        f'http://127.0.0.1:{BACKEND_PORT}',
        f"backend API smoke test must target port {BACKEND_PORT}",
        errors,
    )

    entrypoint_port = _backend_entrypoint_port(root, errors)
    if entrypoint_port != BACKEND_PORT:
        errors.append(f"backend entrypoint must run on port {BACKEND_PORT}")

    _require_text(
        root,
        "README.md",
        f"--port {BACKEND_PORT}",
        f"root README backend command must use port {BACKEND_PORT}",
        errors,
    )
    _require_text(
        root,
        "README.md",
        f"http://localhost:{FRONTEND_PORT}",
        f"root README frontend URL must use port {FRONTEND_PORT}",
        errors,
    )
    _require_text(
        root,
        "backend/job-platform/README.md",
        f"--port {BACKEND_PORT}",
        f"backend README command must use port {BACKEND_PORT}",
        errors,
    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root to validate.",
    )
    args = parser.parse_args()
    errors = collect_consistency_errors(args.root.resolve())
    if errors:
        print("Project consistency checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "Project consistency checks passed "
        f"(frontend={FRONTEND_PORT}, backend={BACKEND_PORT})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
