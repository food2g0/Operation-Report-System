# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec for Operation Report System - CLEAN CLIENT BUILD
Includes ONLY client-side code. Server-side and debug code excluded.
Used by build_secure.py for secure builds with embedded credentials.
"""

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('field_config.json', '.'), ('assets', 'assets'), ('db_config.enc', '.'), ('Client', 'Client')],
    hiddenimports=['cryptography', 'cryptography.fernet', 'cryptography.hazmat.primitives.kdf.pbkdf2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    # ========================================================================
    # EXCLUDE SERVER-SIDE CODE (clean client-only build)
    # ========================================================================
    excludes=[
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
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\logo.ico'],
)
