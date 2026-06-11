# Setup Daily Palawan Migration Scheduler

Write-Host "Setting up Windows Task Scheduler for Daily Palawan Migration..."

$scriptDir = "c:\Users\Admin\Operation-Report-System"
$migrationScript = Join-Path $scriptDir "migrate_palawan_daily.py"
$pythonExe = "python"
$taskName = "Daily Palawan Migration"
$taskDescription = "Automatic daily migration of palawan data from daily_reports to payable_tbl_brand_a at 8:30 AM"

Write-Host "Script: $migrationScript"
Write-Host "Time: 8:30 AM every day"
Write-Host ""

if (-not (Test-Path $migrationScript)) {
    Write-Host "ERROR: Migration script not found at $migrationScript"
    exit 1
}

Write-Host "Migration script found"

$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Found existing task. Removing..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Start-Sleep -Seconds 2
}

Write-Host "Creating task..."
$action = New-ScheduledTaskAction -Execute $pythonExe -Argument $migrationScript -WorkingDirectory $scriptDir
$trigger = New-ScheduledTaskTrigger -Daily -At 08:30AM
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description $taskDescription -Force | Out-Null

Start-Sleep -Seconds 1
$newTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($newTask) {
    Write-Host ""
    Write-Host "SUCCESS! Task created:"
    Write-Host "  Name: $taskName"
    Write-Host "  Schedule: Daily at 8:30 AM"
    Write-Host "  Script: $migrationScript"
    Write-Host ""
    Write-Host "Migration logs: $scriptDir\logs\palawan_migration_YYYYMMDD.log"
} else {
    Write-Host "ERROR: Failed to create task"
    exit 1
}
