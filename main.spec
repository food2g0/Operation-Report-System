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
