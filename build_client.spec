# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for Operation Report System - CLIENT ONLY BUILD
This creates a clean executable with ONLY client-side code
No server, migrations, or debugging tools included
"""

import sys
import os

# Add project root to path for imports
# Use current working directory since __file__ may not be defined in spec context
project_root = os.getcwd()

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
    # DATA FILES - Include only client-side resources
    # ========================================================================
    datas=[
        # Include Client directory with all UI files
        (os.path.join(project_root, 'Client'), 'Client'),
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
)

# ========================================================================
# BUILD CONFIGURATION
# ========================================================================

cipher = None  # No encryption for open source project

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
