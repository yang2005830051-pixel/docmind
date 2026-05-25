@echo off
cd /d "%~dp0"
python setup.py
if errorlevel 1 (
    echo.
    echo [ERROR] Python not found or setup failed
    echo        Please install Python 3.12 from https://www.python.org/downloads/
    echo        Make sure to check "Add Python to PATH"
    pause
)
