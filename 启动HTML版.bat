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
echo   DocMind HTML - Starting...
echo ========================================
echo.
echo   Open http://localhost:8501 in browser
echo.
.venv\Scripts\python -m uvicorn server:app --host 0.0.0.0 --port 8501 --reload
pause
