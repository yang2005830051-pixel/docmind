@echo off
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
    echo [SETUP] First time setup, please wait...
    python setup.py
    if errorlevel 1 (
        echo [ERROR] Setup failed
        pause
        exit /b 1
    )
)

echo ========================================
echo   DocMind - Starting...
echo ========================================
echo.
.venv\Scripts\streamlit run app.py
pause
