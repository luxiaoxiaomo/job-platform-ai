@echo off
chcp 65001 > nul
echo ========================================
echo   Starting frontend dev server
echo ========================================
echo.
cd /d "%~dp0"
echo URL: http://localhost:5175
echo API: http://localhost:8003
echo Press Ctrl+C to stop
echo ========================================
echo.
npm run dev
pause
