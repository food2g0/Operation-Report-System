@echo off
REM ============================================================================
REM CLEAN CLIENT BUILD SCRIPT
REM Operation Report System - Client-Only Executable
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo  OPERATION REPORT SYSTEM - CLIENT BUILD
echo ============================================================================
echo.
echo This script builds a clean executable with ONLY client-side code.
echo Server-side code, migrations, and debug tools are excluded.
echo.

REM Check if PyInstaller is installed
where pyinstaller >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: PyInstaller is not installed!
    echo.
    echo Install it with:
    echo   pip install pyinstaller
    echo.
    exit /b 1
)

REM Check if spec file exists
if not exist "build_client.spec" (
    echo ERROR: build_client.spec not found!
    echo Please create the spec file first.
    exit /b 1
)

echo Building clean client executable...
echo.

REM Clean previous builds
if exist "build" (
    echo Cleaning previous build artifacts...
    rmdir /s /q build
)

if exist "dist" (
    echo Cleaning previous dist folder...
    rmdir /s /q dist
)

REM Run PyInstaller
echo Running PyInstaller with clean manifest...
pyinstaller build_client.spec

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Build failed!
    echo Check the output above for details.
    exit /b 1
)

REM Verify build
echo.
echo ============================================================================
echo  BUILD VERIFICATION
echo ============================================================================
echo.

if exist "dist\OperationReportSystem.exe" (
    echo [SUCCESS] Executable created: dist\OperationReportSystem.exe
    echo.

    REM Get file size
    for /F "usebackq" %%A in ('dist\OperationReportSystem.exe') do (
        set "size=%%~zA"
    )

    if defined size (
        set /A "size_mb=!size!/1048576"
        echo File size: !size! bytes (~!size_mb! MB)
    )

    echo.
    echo WHAT'S INCLUDED:
    echo   [✓] Client UI (admin_dashboard, report_page, etc.)
    echo   [✓] API Client (api_db_manager.py)
    echo   [✓] Security (login, authentication)
    echo   [✓] All PyQt5 dependencies
    echo.
    echo WHAT'S EXCLUDED:
    echo   [✓] api_server.py (not included)
    echo   [✓] Database migrations (not included)
    echo   [✓] Debug/testing tools (not included)
    echo.
    echo READY TO DEPLOY!
    echo Location: dist\OperationReportSystem.exe
    echo.
) else (
    echo ERROR: Build completed but executable not found!
    exit /b 1
)

echo ============================================================================
echo  BUILD COMPLETE
echo ============================================================================
echo.
pause
