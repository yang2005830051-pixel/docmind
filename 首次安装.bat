@echo off
cd /d "%~dp0"
echo ========================================
echo   DocMind - Environment Setup
echo ========================================
echo.

:: Check Python 3.12
echo [Check] Python 3.12...
py -3.12 --version >/dev/null 2>&1
if errorlevel 1 (
    echo [MISSING] Python 3.12 not found
    echo.
    echo [INSTALL] Installing Python 3.12 via winget...
    winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo.
        echo [FAIL] Auto-install failed
        echo        Please manually install from https://www.python.org/downloads/
        echo        Make sure to check "Add Python to PATH"
        pause
        exit /b 1
    )
    echo.
    echo [OK] Python 3.12 installed
    echo      Please re-run this script
    pause
    exit /b 0
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
.venv\Scripts\python -c "import streamlit" >/dev/null 2>&1
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
    copy .env.example .env >/dev/null
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
