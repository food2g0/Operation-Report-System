"""
Secure Configuration Module
- At development: loads from .env file
- At build time: credentials are embedded (no .env needed in bundle)
"""
import os
import sys

def is_bundled():
    """Check if running as PyInstaller bundle"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def get_config():
    """
    Returns database configuration.
    
    For bundled app: uses embedded credentials (set during build)
    For development: loads from .env file
    """
    
    if is_bundled():
        # ============================================
        # EMBEDDED CREDENTIALS (for bundled .exe)
        # These values are set during the build process
        # ============================================
        try:
            # These placeholders are replaced by build_secure.py
            host = '222.127.90.218'
            port_str = '3306'
            user = 'ors_user'
            password = 'ORS_StrongPass_2026!'
            database = 'operation_db'
            
            # Validate that placeholders were replaced
            if host.startswith('__') and host.endswith('__'):
                raise ValueError("Build error: Credentials not embedded. Run build_secure.py")
            
            return {
                'host': host,
                'port': int(port_str) if port_str.isdigit() else 3306,
                'user': user,
                'password': password,
                'database': database
            }
        except Exception as e:
            print(f"Config error: {e}")
            # Fallback to prevent crash
            return {
                'host': 'localhost',
                'port': 3306,
                'user': 'root',
                'password': '',
                'database': 'operation_db'
            }
    else:
        # Development mode - load from .env
        from dotenv import load_dotenv
        load_dotenv()
        
        return {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'operation_db')
        }

# Export config
DB_CONFIG = get_config()
