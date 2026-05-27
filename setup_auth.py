"""生成 Nginx Basic Auth 密码文件。"""

import sys
import getpass
import hashlib
import base64
import os
import secrets
import string


def generate_htpasswd(username: str, password: str) -> str:
    """生成 htpasswd 格式的密码行（SHA1 + salt）。"""
    salt = os.urandom(4)
    h = hashlib.sha1((password + salt.decode("latin-1")).encode("latin-1")).digest()
    encoded = base64.b64encode(h + salt).decode("ascii")
    return f"{username}:{{SSHA}}{encoded}"


def generate_random_password(length: int = 12) -> str:
    """生成随机密码。"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def main():
    print("=" * 40)
    print("  DocMind - 创建登录账号")
    print("=" * 40)

    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
    elif len(sys.argv) == 2:
        # 只提供用户名，自动生成密码
        username = sys.argv[1]
        password = generate_random_password()
        print(f"\n自动生成密码: {password}")
        print("请妥善保存此密码！")
    else:
        username = input("\n用户名: ").strip()
        if not username:
            print("用户名不能为空")
            return
        password = getpass.getpass("密码 (留空自动生成): ").strip()
        if not password:
            password = generate_random_password()
            print(f"\n自动生成密码: {password}")
            print("请妥善保存此密码！")

    line = generate_htpasswd(username, password)
    htpasswd_path = os.path.join(os.path.dirname(__file__), "nginx.htpasswd")

    # 如果文件已存在，追加；否则创建
    mode = "a" if os.path.exists(htpasswd_path) else "w"
    with open(htpasswd_path, mode, encoding="utf-8") as f:
        f.write(line + "\n")

    print(f"\n账号 '{username}' 已创建")
    print(f"密码文件: {htpasswd_path}")
    print("\n现在可以启动: docker-compose up -d")


if __name__ == "__main__":
    main()
