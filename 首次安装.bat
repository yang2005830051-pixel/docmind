@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo   技术文档智能问答 - 环境检查
echo ========================================
echo.

:: 检查 Python
echo [检查] Python 3.12...
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo [缺失] Python 3.12 未安装
    echo        请从 https://www.python.org/downloads/ 下载安装
    echo        安装时务必勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('py -3.12 --version') do set PYVER=%%i
    echo [通过] %PYVER%
)

:: 检查虚拟环境
echo.
echo [检查] 虚拟环境...
if exist .venv\Scripts\python.exe (
    echo [通过] 虚拟环境已存在
) else (
    echo [安装] 创建虚拟环境...
    py -3.12 -m venv .venv
    if errorlevel 1 (
        echo [失败] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo [完成] 虚拟环境创建成功
)

:: 检查依赖
echo.
echo [检查] 项目依赖...
.venv\Scripts\python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [安装] 首次安装依赖（约2-3分钟）...
    .venv\Scripts\pip install -r requirements.txt -q
    if errorlevel 1 (
        echo [失败] 依赖安装失败
        pause
        exit /b 1
    )
    echo [完成] 依赖安装成功
) else (
    echo [通过] 依赖已安装
)

:: 检查环境变量
echo.
echo [检查] 环境配置...
if exist .env (
    echo [通过] .env 配置文件已存在
) else (
    copy .env.example .env >nul
    echo [配置] 已创建 .env 文件
    echo        请用记事本打开 .env，填入你的 API Key
)

:: 完成
echo.
echo ========================================
echo   所有检查通过！
echo.
echo   下次使用直接双击 "启动.bat" 即可
echo ========================================
pause
