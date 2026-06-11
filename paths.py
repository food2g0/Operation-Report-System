r"""
Application Paths Configuration
Separates main app directory (D:\) from cache/temp (AppData\)
"""

import os
from pathlib import Path

# ============================================================================
# APPLICATION ROOT (main program files)
# ============================================================================
# Default: D:\OperationReportSystem\ (user can customize via env var)
APP_ROOT = Path(os.environ.get(
    'ORS_APP_ROOT',
    'D:\\OperationReportSystem'
))

# ============================================================================
# APP DATA (cache, logs, temp files - in AppData)
# ============================================================================
# Automatically uses: %APPDATA%\OperationReportSystem\
APPDATA_ROOT = Path(
    os.environ.get('APPDATA') or os.path.expanduser('~')
) / 'OperationReportSystem'

# ============================================================================
# SUBDIRECTORIES
# ============================================================================

# Main app directories
ASSETS_DIR = APP_ROOT / 'assets'
CONFIG_DIR = APP_ROOT / 'config'

# AppData subdirectories
CACHE_DIR = APPDATA_ROOT / 'cache'
LOGS_DIR = APPDATA_ROOT / 'logs'
DRAFTS_DIR = APPDATA_ROOT / 'drafts'
UPDATE_DIR = APPDATA_ROOT / 'update'

# ============================================================================
# SPECIAL FILES
# ============================================================================

# Update state (stored in AppData)
UPDATE_STATE_FILE = UPDATE_DIR / 'ors_update_state.json'

# Logs
LOG_FILE = LOGS_DIR / f'OperationReportSystem_{__import__("datetime").datetime.now().strftime("%Y%m%d")}.log'

# Draft storage
DRAFTS_FILE = DRAFTS_DIR / 'drafts.json'

# ============================================================================
# INITIALIZATION
# ============================================================================

def ensure_directories():
    """Create all necessary directories on startup."""
    for directory in [CACHE_DIR, LOGS_DIR, DRAFTS_DIR, UPDATE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

def get_app_root():
    """Get application root directory."""
    return str(APP_ROOT)

def get_appdata_root():
    """Get AppData root directory for this application."""
    return str(APPDATA_ROOT)

# Auto-create directories when module is imported
ensure_directories()
