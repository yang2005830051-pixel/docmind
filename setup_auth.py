"""生成 Nginx Basic Auth 密码文件。"""

import sys
import getpass
import hashlib
import base64
import os


def generate_htpasswd(username: str, password: str) -> str:
    """生成 htpasswd 格式的密码行（SHA1 + salt）。"""
    salt = os.urandom(4)
    h = hashlib.sha1((password + salt.decode("latin-1")).encode("latin-1")).digest()
    encoded = base64.b64encode(h + salt).decode("ascii")
    return f"{username}:{{SSHA}}{encoded}"


def main():
    print("=" * 40)
    print("  DocMind - 创建登录账号")
    print("=" * 40)

    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
    else:
        username = input("\n用户名: ").strip()
        if not username:
            print("用户名不能为空")
            return
        password = getpass.getpass("密码: ").strip()
        if not password:
            print("密码不能为空")
            return

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
