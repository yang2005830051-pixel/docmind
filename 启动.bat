@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo   技术文档智能问答系统 - 启动中...
echo ========================================
echo.
.venv\Scripts\streamlit run app.py
pause
