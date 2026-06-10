@echo off
REM Daily Palawan Migration Batch File
REM This batch file runs the palawan migration script
REM Scheduled to run at 8:30 AM daily via Windows Task Scheduler

echo.
echo ========================================
echo Palawan Daily Migration
echo Time: %date% %time%
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Run the Python script
python migrate_palawan_daily.py

REM Check for errors
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Migration failed with exit code %ERRORLEVEL%
    echo.
    exit /b %ERRORLEVEL%
) else (
    echo.
    echo Migration completed successfully
    echo.
    exit /b 0
)
