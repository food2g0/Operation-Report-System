"""
Secure Configuration Manager
Encrypts/decrypts database credentials using Fernet symmetric encryption
"""
import os
import sys
import json
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Application-specific salt and password for key derivation
# These make the encryption unique to this application
_APP_SALT = b'OperationReportSystem2026'
_APP_KEY = b'ORS_SecureKey_X9K2M5'


def _derive_key():
    """Derive encryption key from app-specific values."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_APP_SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(_APP_KEY))
    return Fernet(key)


def _get_config_path():
    """Get the path to the encrypted config file."""
    # For PyInstaller --onefile builds, data is extracted to _MEIPASS
    if getattr(sys, '_MEIPASS', None):
        base_path = Path(sys._MEIPASS)
    # For PyInstaller --onedir builds
    elif getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    # For regular Python execution
    else:
        base_path = Path(__file__).parent
    return base_path / 'db_config.enc'


def encrypt_config(config_dict, output_path=None):
    """
    Encrypt a configuration dictionary and save to file.
    Use this to create the encrypted config file.
    
    Usage:
        from secure_config import encrypt_config
        encrypt_config({
            'host': '222.127.90.218',
            'port': 33306,
            'user': 'ors_user',
            'password': 'ORS_StrongPass_2026!',
            'database': 'operation_db',
        })
    """
    fernet = _derive_key()
    json_data = json.dumps(config_dict).encode()
    encrypted = fernet.encrypt(json_data)
    
    path = Path(output_path) if output_path else _get_config_path()
    path.write_bytes(encrypted)
    print(f"✅ Encrypted config saved to: {path}")
    return path


def decrypt_config():
    """
    Decrypt and return the configuration dictionary.
    Returns None if file doesn't exist or decryption fails.
    """
    path = _get_config_path()
    if not path.exists():
        return None
    
    try:
        fernet = _derive_key()
        encrypted_data = path.read_bytes()
        decrypted = fernet.decrypt(encrypted_data)
        return json.loads(decrypted.decode())
    except Exception as e:
        print(f"⚠️ Failed to decrypt config: {e}")
        return None


def get_db_config():
    """
    Get database configuration.
    Priority: encrypted file > environment variables > defaults
    """
    # Try encrypted config first
    config = decrypt_config()
    if config:
        return config
    
    # Fall back to environment variables
    return {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', '3306')),
        'user': os.getenv('MYSQL_USER', ''),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', ''),
    }


# CLI for generating encrypted config
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'generate':
        # Generate encrypted config from current .env or prompts
        from dotenv import load_dotenv
        load_dotenv()
        
        config = {
            'host': os.getenv('MYSQL_HOST') or input('Host: '),
            'port': int(os.getenv('MYSQL_PORT') or input('Port: ')),
            'user': os.getenv('MYSQL_USER') or input('User: '),
            'password': os.getenv('MYSQL_PASSWORD') or input('Password: '),
            'database': os.getenv('MYSQL_DATABASE') or input('Database: '),
        }
        encrypt_config(config)
    else:
        print("Usage: python secure_config.py generate")
        print("  Generates encrypted db_config.enc from .env or prompts")
