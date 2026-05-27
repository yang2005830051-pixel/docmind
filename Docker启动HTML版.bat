@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   DocMind - Docker 部署
echo ========================================
echo.

:: 检查 Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未安装 Docker，请先安装 Docker Desktop
    echo 下载地址: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

:: 检查 .env
if not exist .env (
    echo [提示] 未找到 .env 文件，正在从模板创建...
    copy .env.example .env >nul
    echo [提示] 请编辑 .env 文件，填入 API Key 后重新运行
    pause
    exit /b 1
)

:: 检查 nginx.htpasswd
if not exist nginx.htpasswd (
    echo [提示] 未找到密码文件，正在创建默认账号...
    echo 默认账号: admin / admin
    echo 建议稍后运行 python setup_auth.py 修改密码
    echo.
    python setup_auth.py admin admin
)

echo 正在启动服务...
echo.

docker-compose up -d --build

if errorlevel 1 (
    echo.
    echo [错误] 启动失败，请检查 Docker 是否正常运行
    pause
    exit /b 1
)

echo.
echo ========================================
echo   启动成功!
echo   访问地址: http://localhost
echo   账号: admin
echo   密码: admin
echo ========================================
echo.
echo 常用命令:
echo   查看日志:  docker-compose logs -f
echo   停止服务:  docker-compose down
echo   重启服务:  docker-compose restart
echo.
pause
