@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
echo ========================================
echo   DocMind - Environment Setup
echo ========================================
echo.

:: Check Python
echo [Check] Python 3.12...
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo [MISSING] Python 3.12 not found
    echo        Please install from https://www.python.org/downloads/
    echo        Make sure to check "Add Python to PATH"
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('py -3.12 --version') do set PYVER=%%i
    echo [OK] %PYVER%
)

:: Check venv
echo.
echo [Check] Virtual environment...
if exist .venv\Scripts\python.exe (
    echo [OK] Virtual environment exists
) else (
    echo [INSTALL] Creating virtual environment...
    py -3.12 -m venv .venv
    if errorlevel 1 (
        echo [FAIL] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [DONE] Virtual environment created
)

:: Check dependencies
echo.
echo [Check] Dependencies...
.venv\Scripts\python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] Installing dependencies (about 2-3 min)...
    .venv\Scripts\pip install -r requirements.txt -q
    if errorlevel 1 (
        echo [FAIL] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [DONE] Dependencies installed
) else (
    echo [OK] Dependencies installed
)

:: Check .env
echo.
echo [Check] Environment config...
if exist .env (
    echo [OK] .env file exists
) else (
    copy .env.example .env >nul
    echo [CONFIG] Created .env file
)

:: Done
echo.
echo ========================================
echo   All checks passed!
echo.
echo   Double-click "启动.bat" to start
echo ========================================
pause
