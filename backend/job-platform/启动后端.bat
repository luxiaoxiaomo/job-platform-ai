@echo off
chcp 65001 > nul
echo ========================================
echo   Starting backend API server
echo ========================================
echo.
cd /d "%~dp0"
echo URL: http://localhost:8003/docs
echo Press Ctrl+C to stop
echo ========================================
echo.
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8003
pause
