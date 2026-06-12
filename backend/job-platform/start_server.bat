@echo off
chcp 65001 > nul
echo ========================================
echo   Starting FastAPI Server
echo ========================================
echo.
cd /d "%~dp0"
echo Working directory: %CD%
echo.
echo Starting uvicorn on port 8003...
.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8003 --reload
