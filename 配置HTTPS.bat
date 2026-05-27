@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   DocMind - 配置 HTTPS
echo ========================================
echo.

if "%~1"=="" (
    echo 用法: 配置HTTPS.bat [域名或IP]
    echo 示例: 配置HTTPS.bat docmind.example.com
    echo 示例: 配置HTTPS.bat 192.168.1.100
    echo.
    echo 如果是本地测试，可以使用:
    echo   配置HTTPS.bat localhost
    pause
    exit /b 1
)

set DOMAIN=%~1

:: 创建 SSL 目录
if not exist ssl mkdir ssl

:: 检查是否为 IP 地址
echo %DOMAIN% | findstr /r "^[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*$" >nul
if %errorlevel%==0 (
    echo [提示] 检测到 IP 地址，将使用自签名证书
    echo.
    echo 正在生成自签名证书...
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout ssl\key.pem -out ssl\cert.pem -subj "/CN=%DOMAIN%" -addext "subjectAltName=IP:%DOMAIN%"
) else (
    echo [提示] 检测到域名，需要使用 Let's Encrypt
    echo.
    echo 请在 Linux 服务器上运行 setup_https.sh 脚本
    echo 或者手动将证书文件放到 ssl 目录:
    echo   ssl\cert.pem - 证书文件
    echo   ssl\key.pem  - 私钥文件
    pause
    exit /b 1
)

echo.
echo ========================================
echo   证书生成完成!
echo ========================================
echo.
echo 重启服务:
echo   docker-compose down
echo   docker-compose up -d
echo.
echo 访问地址: https://%DOMAIN%
echo.
pause
