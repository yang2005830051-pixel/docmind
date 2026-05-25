@echo off
cd /d "%~dp0"
echo ========================================
echo   DocMind - Starting...
echo ========================================
echo.
.venv\Scripts\streamlit run app.py
pause
