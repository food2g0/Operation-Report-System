# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for Operation Report System - CLIENT ONLY BUILD
This creates a clean executable with ONLY client-side code
No server, migrations, or debugging tools included
"""

import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))

a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],

    # ========================================================================
    # BINARY DEPENDENCIES - Only include what client needs
    # ========================================================================
    binaries=[],

    # ========================================================================
    # HIDDEN IMPORTS - Modules PyInstaller might not detect
    # ========================================================================
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtPrintSupport',
        'PyQt5.QtSvg',
        'requests',
        'jwt',
        'bcrypt',
        'dotenv',
        'logging_config',
    ],

    # ========================================================================
    # MODULE EXCLUSIONS - Server-side code to exclude
    # ========================================================================
    excludedimports=[
        # FastAPI/Server
        'api_server',
        'fastapi',
        'starlette',
        'uvicorn',

        # Database
        'db_connect_pooled',
        'db_manager',
        'error_tracker',
        'secure_config',
        'api_config',

        # Migration/Admin
        'migrate_palawan_daily',
        'migrate_palawan_complete',
        'backfill_palawan_to_payable',
        'setup_database_indexes',
        'device_trust',

        # Testing/Debugging
        'load_test',
        'locustfile',
        'test_connection',
        'test_corp_filter',
        'debug_audit_single_report',
        'debug_corp_branches',
        'find_report_b',
        'fix_missing_branches',
        'inspect_daily_reports',
        'refresh_summary',
        'verify_api_setup',
        'update_field_config_db',
        'clear_all_data',
        'analyze_credit_total',
        'build_secure',

        # Server-specific modules
        'redis',
        'sqlalchemy',
        'gunicorn',
    ],

    # ========================================================================
    # DATA FILES - Include only client-side resources
    # ========================================================================
    datas=[
        # Include Client directory with all UI files
        (os.path.join(project_root, 'Client'), 'Client'),
        # Include config template if exists
        (os.path.join(project_root, 'config.py'), '.') if os.path.exists(os.path.join(project_root, 'config.py')) else None,
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
)

# ========================================================================
# BUILD CONFIGURATION
# ========================================================================

pyz = PYZ(a.pure, a.zipped_data, cipher=cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,

    [],
    name='OperationReportSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,

    # Icon (if available)
    icon=None,  # Set to 'icon.ico' if you have one

    # Metadata
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# ========================================================================
# OPTIONAL: Collect into a directory instead of single executable
# ========================================================================
# Uncomment to use onedir instead of onefile
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='OperationReportSystem'
# )

# ========================================================================
# BUILD NOTES
# ========================================================================
"""
TO BUILD:
  pyinstaller build_client.spec

RESULT:
  dist/OperationReportSystem.exe (Windows)

OPTIONS:
  - Modify console=False to console=True for debugging
  - Add icon parameter: icon='path/to/icon.ico'
  - Change name parameter to customize executable name

VERIFICATION:
  After building, verify the .exe contains no server files:
  - Use 7-Zip or similar to inspect the executable
  - Should see Client/ directory, not api_server.py
  - Should see ~40 Python modules, not 70+

OPTIMIZATION:
  - UPX compresses the executable (~30% size reduction)
    Download from: https://upx.github.io/
  - Or set upx=False if UPX not installed
"""
