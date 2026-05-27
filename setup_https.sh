#!/bin/bash
# DocMind - HTTPS 证书配置脚本
# 使用 Let's Encrypt 免费证书

set -e

echo "========================================"
echo "  DocMind - 配置 HTTPS"
echo "========================================"
echo ""

# 检查参数
if [ -z "$1" ]; then
    echo "用法: ./setup.sh <域名或IP>"
    echo "示例: ./setup.sh docmind.example.com"
    echo "示例: ./setup.sh 192.168.1.100"
    exit 1
fi

DOMAIN=$1
EMAIL="${2:-admin@$DOMAIN}"

# 检查是否为 IP 地址
if [[ $DOMAIN =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "[提示] 检测到 IP 地址，将使用自签名证书"
    USE_SELF_SIGNED=true
else
    echo "[提示] 检测到域名，将使用 Let's Encrypt 证书"
    USE_SELF_SIGNED=false
fi

# 创建 SSL 目录
mkdir -p ssl

if [ "$USE_SELF_SIGNED" = true ]; then
    # 生成自签名证书（IP 地址用）
    echo "正在生成自签名证书..."
    openssl req -x509 -nodes -days 3650 \
        -newkey rsa:2048 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -subj "/CN=$DOMAIN" \
        -addext "subjectAltName=IP:$DOMAIN"
    echo "自签名证书已生成（有效期 10 年）"
else
    # 使用 Let's Encrypt
    echo "正在获取 Let's Encrypt 证书..."

    # 检查 certbot 是否安装
    if ! command -v certbot &> /dev/null; then
        echo "[错误] 未安装 certbot，请先安装:"
        echo "  Ubuntu/Debian: sudo apt install certbot"
        echo "  CentOS/RHEL: sudo yum install certbot"
        exit 1
    fi

    # 停止 nginx 以释放 80 端口
    docker-compose stop nginx 2>/dev/null || true

    # 获取证书
    certbot certonly --standalone \
        -d "$DOMAIN" \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email

    # 复制证书到项目目录
    cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/cert.pem
    cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/key.pem

    echo "Let's Encrypt 证书已获取"
fi

# 更新 nginx 配置
echo "正在更新 nginx 配置..."
cat > nginx.conf << 'EOF'
# HTTP -> HTTPS 重定向
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

# HTTPS 配置
server {
    listen 443 ssl;
    server_name _;

    # SSL 证书
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # SSL 优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 请求体大小限制（上传文件用）
    client_max_body_size 50M;

    # Basic Auth 认证
    auth_basic "DocMind - 请输入账号密码";
    auth_basic_user_file /etc/nginx/.htpasswd;

    # 代理到 FastAPI 后端
    location / {
        proxy_pass http://app:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    # 健康检查不需要认证
    location /health {
        auth_basic off;
        proxy_pass http://app:8501/health;
    }
}
EOF

# 更新 docker-compose.yml 添加 SSL 卷
echo "正在更新 docker-compose.yml..."
if ! grep -q "ssl" docker-compose.yml; then
    sed -i '/nginx.htpasswd/a\      - ./ssl:/etc/nginx/ssl:ro' docker-compose.yml
fi

echo ""
echo "========================================"
echo "  HTTPS 配置完成!"
echo "========================================"
echo ""
if [ "$USE_SELF_SIGNED" = true ]; then
    echo "证书类型: 自签名（浏览器会显示警告，点击继续即可）"
else
    echo "证书类型: Let's Encrypt（受浏览器信任）"
fi
echo ""
echo "重启服务:"
echo "  docker-compose down"
echo "  docker-compose up -d"
echo ""
echo "访问地址: https://$DOMAIN"
echo ""
