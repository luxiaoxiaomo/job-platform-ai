@echo off
chcp 65001 > nul
cd /d D:\AIposition\backend\job-platform
echo [%date% %time%] starting backend 8003 > backend_8003_codex_wrapper.log
echo cwd=%cd% >> backend_8003_codex_wrapper.log
"D:\AIposition\backend\job-platform\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8003 >> backend_8003_codex_wrapper.log 2>&1
echo [%date% %time%] backend exited with %errorlevel% >> backend_8003_codex_wrapper.log
