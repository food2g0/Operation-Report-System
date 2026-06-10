# ============================================================================
# CLEAN CLIENT BUILD SCRIPT (PowerShell)
# Operation Report System - Client-Only Executable
# ============================================================================

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host " OPERATION REPORT SYSTEM - CLIENT BUILD" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script builds a clean executable with ONLY client-side code." -ForegroundColor Green
Write-Host "Server-side code, migrations, and debug tools are excluded." -ForegroundColor Green
Write-Host ""

# Check if PyInstaller is installed
try {
    $pyinstaller = Get-Command pyinstaller -ErrorAction Stop
    Write-Host "[OK] PyInstaller found: $($pyinstaller.Source)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] PyInstaller is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install it with:" -ForegroundColor Yellow
    Write-Host "  pip install pyinstaller" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Check if spec file exists
if (-not (Test-Path "build_client.spec")) {
    Write-Host "[ERROR] build_client.spec not found!" -ForegroundColor Red
    Write-Host "Please create the spec file first." -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Spec file found: build_client.spec" -ForegroundColor Green
Write-Host ""

# Clean previous builds
Write-Host "Cleaning previous build artifacts..." -ForegroundColor Yellow

if (Test-Path "build") {
    Remove-Item -Recurse -Force "build" -ErrorAction SilentlyContinue
    Write-Host "  [OK] Removed ./build" -ForegroundColor Green
}

if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist" -ErrorAction SilentlyContinue
    Write-Host "  [OK] Removed ./dist" -ForegroundColor Green
}

Write-Host ""
Write-Host "Running PyInstaller with clean manifest..." -ForegroundColor Yellow
Write-Host ""

# Run PyInstaller
& pyinstaller build_client.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[✗] ERROR: Build failed!" -ForegroundColor Red
    Write-Host "Check the output above for details." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host " BUILD VERIFICATION" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Verify build
$exePath = "dist\OperationReportSystem.exe"

if (Test-Path $exePath) {
    Write-Host "[OK] Executable created successfully!" -ForegroundColor Green
    Write-Host ""

    # Get file size
    $fileSize = (Get-Item $exePath).Length
    $fileSizeMB = [math]::Round($fileSize / 1MB, 2)

    Write-Host "File: $exePath" -ForegroundColor White
    Write-Host "Size: $($fileSize:N0) bytes (~$fileSizeMB MB)" -ForegroundColor White
    Write-Host ""

    Write-Host "WHAT'S INCLUDED:" -ForegroundColor Green
    Write-Host "  [OK] Client UI (admin_dashboard, report_page, etc.)" -ForegroundColor Green
    Write-Host "  [OK] API Client (api_db_manager.py)" -ForegroundColor Green
    Write-Host "  [OK] Security (login, authentication)" -ForegroundColor Green
    Write-Host "  [OK] All PyQt5 dependencies" -ForegroundColor Green
    Write-Host ""

    Write-Host "WHAT'S EXCLUDED:" -ForegroundColor Yellow
    Write-Host "  [OK] api_server.py (not included)" -ForegroundColor Yellow
    Write-Host "  [OK] Database migrations (not included)" -ForegroundColor Yellow
    Write-Host "  [OK] Debug/testing tools (not included)" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "READY TO DEPLOY!" -ForegroundColor Green
    Write-Host "Location: $exePath" -ForegroundColor Cyan
    Write-Host ""

} else {
    Write-Host "[ERROR] Build completed but executable not found!" -ForegroundColor Red
    exit 1
}

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host " BUILD COMPLETE" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Offer to open dist folder
$response = Read-Host "Open dist folder? (y/n)"
if ($response -eq 'y') {
    explorer.exe "dist"
}
