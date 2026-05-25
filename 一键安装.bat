@echo off
cd /d "%~dp0"

echo ========================================
echo   DocMind - One-Click Install
echo ========================================
echo.

:: Check git
git --version >NUL 2>&1
if errorlevel 1 (
    echo [ERROR] Git not found
    echo        Please install from https://git-scm.com/downloads
    pause
    exit /b 1
)

:: Check Python
py -3.12 --version >NUL 2>&1
if errorlevel 1 (
    echo [INFO] Python 3.12 not found, installing via winget...
    winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo [ERROR] Python install failed
        echo        Please install from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo [OK] Python 3.12 installed
    echo.
)

:: Clone repo
if exist docmind (
    echo [INFO] docmind folder already exists, skipping clone
) else (
    echo [INFO] Downloading code...
    git clone https://github.com/yang2005830051-pixel/docmind.git
    if errorlevel 1 (
        echo [ERROR] Clone failed
        pause
        exit /b 1
    )
)

cd docmind

:: Run setup
echo.
echo [INFO] Running setup...
python setup.py

:: Start app
echo.
echo [INFO] Starting DocMind...
start cmd /c "cd /d "%~dp0docmind" && .venv\Scripts\streamlit run app.py"
