"""
Secure Build Script for PyInstaller + Inno Setup
Embeds credentials from .env into config.py at build time

Usage:
    python build_secure.py           # Build .exe only
    python build_secure.py --installer  # Build .exe + create installer
"""
import os
import sys
import shutil
import subprocess
from dotenv import load_dotenv


def find_inno_setup():
    """Find Inno Setup compiler path"""
    common_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    return None


def build_secure(create_installer=False):
    print("=" * 60)
    print("  SECURE BUILD PROCESS")
    print("  Credentials will be embedded - NO .env in output")
    print("=" * 60)
    
    # Load .env
    load_dotenv()
    
    # Validate credentials exist
    required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"\n[ERROR] Missing required .env variables: {', '.join(missing)}")
        print("Please ensure .env file exists with all database credentials.")
        return False
    
    # Get credentials
    credentials = {
        '__MYSQL_HOST__': os.getenv('MYSQL_HOST'),
        '__MYSQL_PORT__': os.getenv('MYSQL_PORT', '3306'),
        '__MYSQL_USER__': os.getenv('MYSQL_USER'),
        '__MYSQL_PASSWORD__': os.getenv('MYSQL_PASSWORD'),
        '__MYSQL_DATABASE__': os.getenv('MYSQL_DATABASE')
    }
    
    # Backup original config.py
    config_path = 'config.py'
    backup_path = 'config.py.backup'
    
    print("\n[1/5] Backing up config.py...")
    shutil.copy(config_path, backup_path)
    
    try:
        # Read and replace placeholders
        print("[2/5] Embedding credentials into config.py...")
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for placeholder, value in credentials.items():
            content = content.replace(placeholder, value)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("      Credentials embedded (hidden from output for security)")
        
        # Run PyInstaller WITHOUT .env  (uses main.spec so field_config.json is bundled)
        print("[3/5] Running PyInstaller (no .env bundled)...")
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            'main.spec'
        ]
        
        result = subprocess.run(cmd, check=True)
        print("\n      PyInstaller completed successfully!")
        print("      Output: dist/main.exe")
        
        # Create installer if requested
        if create_installer:
            print("\n[4/5] Creating installer with Inno Setup...")
            iscc_path = find_inno_setup()
            
            if not iscc_path:
                print("      [WARNING] Inno Setup not found. Skipping installer creation.")
                print("      Install from: https://jrsoftware.org/isinfo.php")
            else:
                # Create installer output directory
                os.makedirs('installer', exist_ok=True)
                
                subprocess.run([iscc_path, 'installer.iss'], check=True)
                print("\n      Installer created: installer/ORS_Setup.exe")
        else:
            print("\n[4/5] Skipping installer (use --installer flag to create)")
        
        print("\n[5/5] Build completed successfully!")
        print("\n" + "=" * 60)
        print("  OUTPUT FILES:")
        print("    - dist/main.exe (standalone executable)")
        if create_installer and find_inno_setup():
            print("    - installer/ORS_Setup.exe (installer)")
        print("\n  SECURITY: No .env file included - credentials embedded in .exe")
        print("=" * 60)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed: {e}")
        return False
        
    finally:
        # Always restore original config.py
        print("\nRestoring original config.py...")
        if os.path.exists(backup_path):
            shutil.move(backup_path, config_path)
            print("Original config.py restored (placeholders back)")


if __name__ == '__main__':
    create_installer = '--installer' in sys.argv
    build_secure(create_installer=create_installer)
