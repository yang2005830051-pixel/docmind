@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
echo ========================================
echo   DocMind - Starting...
echo ========================================
echo.
.venv\Scripts\streamlit run app.py
pause
