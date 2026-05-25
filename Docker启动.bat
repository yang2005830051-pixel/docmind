@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
echo ========================================
echo   DocMind - Docker Start
echo ========================================
echo.
docker compose up
pause
