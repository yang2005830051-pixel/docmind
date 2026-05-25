@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo   技术文档智能问答系统 - Docker启动
echo ========================================
echo.
docker compose up
pause
