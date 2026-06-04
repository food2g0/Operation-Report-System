"""
Secure Build Script for PyInstaller + Inno Setup
Embeds credentials from .env into config.py at build time.

► The ONLY file you need to edit for a new release is version.py ◄
  This script reads __version__ from version.py automatically and
  updates installer.iss before building.

Usage:
    python build_secure.py             # Build .exe only
    python build_secure.py --installer # Build .exe + create ORS_Setup.exe
"""
import os
import re
import sys
import shutil
import subprocess
from dotenv import load_dotenv


def get_version():
    """Read __version__ from version.py without importing it."""
    with open('version.py', 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    if not match:
        raise RuntimeError("Could not find __version__ in version.py")
    return match.group(1)


def patch_installer_iss(version):
    """Update AppVersion in installer.iss to match version.py."""
    iss_path = 'installer.iss'
    with open(iss_path, 'r', encoding='utf-8') as f:
        content = f.read()
    updated = re.sub(r'^(AppVersion\s*=\s*).*$', rf'\g<1>{version}', content, flags=re.MULTILINE)
    if updated == content:
        print(f"      installer.iss already at v{version}")
    else:
        with open(iss_path, 'w', encoding='utf-8') as f:
            f.write(updated)
        print(f"      installer.iss patched → AppVersion={version}")


def find_inno_setup():
    for path in [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]:
        if os.path.exists(path):
            return path
    return None


def build_secure(create_installer=False):
    print("=" * 60)
    print("  SECURE BUILD PROCESS")
    print("  Credentials will be embedded - NO .env in output")
    print("=" * 60)

    # ── Read version (single source of truth: version.py) ─────────────────
    try:
        app_version = get_version()
    except Exception as e:
        print(f"\n[ERROR] Could not read version.py: {e}")
        return False
    print(f"\n  Building version: v{app_version}")

    # Load .env
    load_dotenv()

    required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        print(f"\n[ERROR] Missing required .env variables: {', '.join(missing)}")
        return False

    credentials = {
        '__MYSQL_HOST__':     os.getenv('MYSQL_HOST'),
        '__MYSQL_PORT__':     os.getenv('MYSQL_PORT', '33306'),
        '__MYSQL_USER__':     os.getenv('MYSQL_USER'),
        '__MYSQL_PASSWORD__': os.getenv('MYSQL_PASSWORD'),
        '__MYSQL_DATABASE__': os.getenv('MYSQL_DATABASE'),
    }

    config_path = 'config.py'
    backup_path = 'config.py.backup'

    print("\n[1/5] Backing up config.py...")
    shutil.copy(config_path, backup_path)

    try:
        print("[2/5] Embedding credentials into config.py...")
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for placeholder, value in credentials.items():
            content = content.replace(placeholder, value)
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("      Credentials embedded (hidden from output for security)")

        print("[3/5] Running PyInstaller...")
        subprocess.run([sys.executable, '-m', 'PyInstaller', '--clean', 'main.spec'], check=True)
        print(f"\n      PyInstaller completed → dist/main.exe  (v{app_version})")

        if create_installer:
            print("\n[4/5] Patching installer.iss and building with Inno Setup...")
            patch_installer_iss(app_version)
            iscc_path = find_inno_setup()
            if not iscc_path:
                print("      [WARNING] Inno Setup not found — skipping installer.")
                print("      Download from: https://jrsoftware.org/isinfo.php")
            else:
                os.makedirs('installer', exist_ok=True)
                # Delete old installer first — Windows Defender locks it and
                # causes Inno Setup error 110 (EndUpdateResource failed)
                old = os.path.join('installer', 'ORS_Setup.exe')
                if os.path.exists(old):
                    os.remove(old)
                    print("      Removed old ORS_Setup.exe")
                subprocess.run([iscc_path, 'installer.iss'], check=True)
                print(f"\n      Installer created → installer/ORS_Setup.exe  (v{app_version})")
        else:
            print("\n[4/5] Skipping installer (add --installer flag to build it)")

        print("\n[5/5] Build completed successfully!")
        print("\n" + "=" * 60)
        print("  OUTPUT FILES:")
        print(f"    dist/main.exe              v{app_version}")
        if create_installer and find_inno_setup():
            print(f"    installer/ORS_Setup.exe    v{app_version}  ← upload this to GitHub")
        print("\n  SECURITY: credentials embedded in .exe, no .env bundled")
        print("=" * 60)
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed: {e}")
        return False

    finally:
        print("\nRestoring original config.py...")
        if os.path.exists(backup_path):
            shutil.move(backup_path, config_path)
            print("config.py restored (placeholders back)")


if __name__ == '__main__':
    build_secure(create_installer='--installer' in sys.argv)
