@echo off
echo ========================================
echo   空岗信息发布对接平台 - 原型演示
echo ========================================
echo.
echo 正在启动本地服务器...
echo.

cd /d "%~dp0"

REM 检查是否安装了 Python
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo 使用 Python 启动服务器...
    echo 原型地址: http://localhost:8080
    echo.
    echo 按 Ctrl+C 可停止服务器
    echo ========================================
    python -m http.server 8080 -d dist
    goto :end
)

REM 检查是否安装了 Node.js
where node >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo 使用 Node.js 启动服务器...
    echo 原型地址: http://localhost:8080
    echo.
    echo 按 Ctrl+C 可停止服务器
    echo ========================================
    npx --yes serve -s dist -l 8080
    goto :end
)

echo [错误] 未检测到 Python 或 Node.js
echo 请安装其中之一后再运行此脚本
echo.
echo Python 下载: https://www.python.org/downloads/
echo Node.js 下载: https://nodejs.org/
pause

:end
