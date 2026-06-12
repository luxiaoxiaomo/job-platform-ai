@echo off
echo ========================================
echo   启动前端服务
echo ========================================
echo.

cd /d "%~dp0"

echo 正在启动前端...
echo 访问 http://localhost:5174 查看应用
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

npm run dev

pause
