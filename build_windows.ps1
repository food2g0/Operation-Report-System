<#
PowerShell build script for creating a production Windows executable
Prerequisites:
- Python 3.8+ on PATH
- Inno Setup (optional) to produce an installer (ISCC on PATH)
#>

set -e

Write-Host "Starting Windows production build..."

# Create a virtual environment for builds
if (-Not (Test-Path -Path .venv_build)) {
    python -m venv .venv_build
}

# Activate venv (PowerShell)
. .\.venv_build\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r Requirements.txt
pip install pyinstaller

# Use existing spec if present, otherwise build from main.py
if (Test-Path -Path main.spec) {
    pyinstaller --clean --noconfirm main.spec
} else {
    pyinstaller --onefile --windowed --icon=assets\logo.ico --add-data ".env;." main.py
}

if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

Write-Host "PyInstaller build complete. Dist contents:";
Get-ChildItem -Path dist -Recurse | Select-Object FullName, Length

# Optional: build installer with Inno Setup Compiler (ISCC)
if (Get-Command iscc -ErrorAction SilentlyContinue) {
    Write-Host "ISCC found — building installer using installer.iss"
    iscc installer.iss
} else {
    Write-Host "ISCC not found. Skipping installer creation. Install Inno Setup to enable this step."
}

Write-Host "Build finished. Sign the executable if you have a code-signing certificate."
