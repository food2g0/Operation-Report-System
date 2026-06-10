# PowerShell Script to Set Up Daily Palawan Migration Task
# Run this script as Administrator to schedule the migration to run at 8:30 AM daily

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$batchFile = Join-Path $scriptDir "run_palawan_migration.bat"

# Task details
$taskName = "Palawan Daily Migration"
$taskDescription = "Automatically migrates palawan details from daily_reports to payable_tbl_brand_a at 8:30 AM daily"
$taskTime = "08:30:00"

# Check if running as Administrator
$isAdmin = ([System.Security.Principal.WindowsIdentity]::GetCurrent().Groups -match "S-1-5-32-544")
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setting up Palawan Daily Migration Task" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if batch file exists
if (-not (Test-Path $batchFile)) {
    Write-Host "ERROR: Batch file not found at: $batchFile" -ForegroundColor Red
    exit 1
}

Write-Host "Batch file location: $batchFile" -ForegroundColor Green
Write-Host "Task will run daily at: $taskTime" -ForegroundColor Green
Write-Host ""

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task: $taskName" -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Start-Sleep -Seconds 1
}

# Create the task trigger (daily at 8:30 AM)
$trigger = New-ScheduledTaskTrigger -Daily -At $taskTime
Write-Host "Task trigger created: Daily at $taskTime" -ForegroundColor Green

# Create the task action
$action = New-ScheduledTaskAction -Execute $batchFile -WorkingDirectory $scriptDir
Write-Host "Task action created: Execute $batchFile" -ForegroundColor Green

# Create task settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RunWithoutNetwork -MultipleInstancePolicy Parallel

# Create the task
try {
    Register-ScheduledTask -TaskName $taskName `
                          -Trigger $trigger `
                          -Action $action `
                          -Settings $settings `
                          -Description $taskDescription `
                          -RunLevel Highest `
                          -Force

    Write-Host ""
    Write-Host "✓ Task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $taskName" -ForegroundColor Green
    Write-Host "  Schedule: Daily at $taskTime" -ForegroundColor Green
    Write-Host "  Script: $batchFile" -ForegroundColor Green
    Write-Host "  Run Level: Highest (Admin)" -ForegroundColor Green
    Write-Host ""

    # Show the task info
    Write-Host "Current Task Configuration:" -ForegroundColor Cyan
    Get-ScheduledTask -TaskName $taskName | Format-List -Property TaskName, Description, State

    Write-Host ""
    Write-Host "Log files will be saved to: $scriptDir\logs\" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "You can manually run the task anytime with:" -ForegroundColor Cyan
    Write-Host "  Start-ScheduledTask -TaskName `"$taskName`"" -ForegroundColor White
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to create scheduled task" -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Setup complete!" -ForegroundColor Green
