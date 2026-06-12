@echo off
echo ========================================
echo   启动后端服务
echo ========================================
echo.

cd /d "%~dp0"

echo 正在启动后端...
echo 访问 http://localhost:8001/docs 查看API文档
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

pause
