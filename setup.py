import subprocess
import sys
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent
VENV_DIR = BASE_DIR / ".venv"
PYTHON = sys.executable


def run(cmd, **kw):
    print(f"  > {cmd}")
    return subprocess.run(cmd, shell=True, cwd=str(BASE_DIR), **kw)


def find_python():
    for cmd in ["py -3.12", "python3.12", "python3", "python"]:
        r = run(f"{cmd} --version", capture_output=True, text=True)
        if r.returncode == 0 and "3.12" in r.stdout:
            return cmd
    return None


def main():
    print("=" * 40)
    print("  DocMind - Environment Setup")
    print("=" * 40)
    print()

    # Check Python
    print("[1/4] Checking Python 3.12...")
    py_cmd = find_python()
    if not py_cmd:
        print("[FAIL] Python 3.12 not found")
        print("       Please install from https://www.python.org/downloads/")
        input("       Press Enter to exit...")
        return
    print(f"  OK: {py_cmd}")

    # Create venv
    print()
    print("[2/4] Creating virtual environment...")
    if VENV_DIR.exists():
        print("  OK: Already exists")
    else:
        r = run(f"{py_cmd} -m venv .venv")
        if r.returncode != 0:
            print("[FAIL] Failed to create virtual environment")
            input("       Press Enter to exit...")
            return
        print("  OK: Created")

    # Install dependencies
    print()
    print("[3/4] Installing dependencies (about 2-3 min)...")
    pip = VENV_DIR / "Scripts" / "pip.exe"
    req = BASE_DIR / "requirements.txt"
    if req.exists():
        r = run(f'"{pip}" install -r "{req}" -q')
        if r.returncode != 0:
            print("[FAIL] Failed to install dependencies")
            input("       Press Enter to exit...")
            return
    print("  OK: Installed")

    # Check .env
    print()
    print("[4/4] Checking config...")
    env_file = BASE_DIR / ".env"
    env_example = BASE_DIR / ".env.example"
    if env_file.exists():
        print("  OK: .env exists")
    elif env_example.exists():
        shutil.copy(env_example, env_file)
        print("  OK: Created .env from template")
    else:
        print("  WARN: No .env or .env.example found")

    print()
    print("=" * 40)
    print("  All checks passed!")
    print()
    print('  Double-click "启动.bat" to start')
    print("=" * 40)
    input("  Press Enter to exit...")


if __name__ == "__main__":
    main()
