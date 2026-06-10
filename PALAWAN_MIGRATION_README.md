# Palawan Daily Migration Setup

This system automatically migrates palawan details from `daily_reports` and `daily_reports_brand_a` tables to `payable_tbl_brand_a` table every day at **8:30 AM**.

## Files Included

1. **migrate_palawan_daily.py** - Main migration script
   - Checks for duplicates before migration
   - Automatically deletes migrated records from source tables
   - Logs all activity to `logs/` directory

2. **run_palawan_migration.bat** - Batch file to execute the Python script

3. **setup_palawan_migration_task.ps1** - PowerShell script to set up Windows Task Scheduler

## How It Works

### Migration Process
1. ✓ Finds all records with palawan data in `daily_reports` (Brand B)
2. ✓ Checks if each record already exists in `payable_tbl_brand_a` (duplicate check)
3. ✓ If NOT a duplicate:
   - Inserts the record into `payable_tbl_brand_a`
   - **Automatically deletes/clears the palawan columns from `daily_reports`**
4. ✓ Repeats the same process for `daily_reports_brand_a` (Brand A)
5. ✓ Logs all activity to timestamped log files

### Duplicate Prevention
- Before migrating, the script checks if a record with the same (corporation, branch, date) already exists in `payable_tbl_brand_a`
- If it exists, the record is skipped and logged as "SKIPPED (duplicate)"
- No duplicates will be created

### Data Cleanup
- After successful migration to `payable_tbl_brand_a`, all palawan columns in the source table are set to 0
- This prevents the same data from being migrated multiple times
- Original records are preserved (not deleted), only the palawan data is cleared

## Setup Instructions

### Option 1: Automatic Setup (Recommended)

1. **Open PowerShell as Administrator**
   - Right-click PowerShell → "Run as Administrator"

2. **Run the setup script:**
   ```powershell
   cd "c:\Users\Admin\Operation-Report-System"
   .\setup_palawan_migration_task.ps1
   ```

3. **Verify the task was created:**
   ```powershell
   Get-ScheduledTask -TaskName "Palawan Daily Migration"
   ```

The task will now automatically run every day at 8:30 AM.

### Option 2: Manual Setup via Task Scheduler

1. **Open Windows Task Scheduler**
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create New Task**
   - Click "Create Task" in the right panel
   - Name: `Palawan Daily Migration`
   - Description: `Automatically migrates palawan details from daily_reports to payable_tbl_brand_a at 8:30 AM daily`
   - ✓ Check "Run with highest privileges"

3. **Set Trigger**
   - Go to "Triggers" tab
   - Click "New..."
   - Begin the task: "On a schedule"
   - Daily at 08:30:00
   - Click "OK"

4. **Set Action**
   - Go to "Actions" tab
   - Click "New..."
   - Action: "Start a program"
   - Program/script: `c:\Users\Admin\Operation-Report-System\run_palawan_migration.bat`
   - Start in: `c:\Users\Admin\Operation-Report-System`
   - Click "OK"

5. **Configure Settings**
   - Go to "Settings" tab
   - ✓ Allow task to be run on demand
   - ✓ Run task as soon as possible after a scheduled start is missed
   - ✓ If the task fails, restart every 1 minute (up to 10 retries)
   - Click "OK"

## Monitoring and Logs

### View Migration Logs
Logs are saved in the `logs/` directory with daily timestamps:
```
c:\Users\Admin\Operation-Report-System\logs\palawan_migration_20260610.log
```

Each log file contains:
- Migration start/end times
- Number of records found and migrated
- Duplicate records skipped
- Records deleted from source tables
- Any errors encountered

### Check Task Status

**View last run status:**
```powershell
Get-ScheduledTask -TaskName "Palawan Daily Migration" | Get-ScheduledTaskInfo
```

**View task history:**
```powershell
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" | Where-Object {$_.Message -like "*Palawan*"}
```

### Manually Run the Migration

**Run immediately (no need to wait for 8:30 AM):**
```powershell
Start-ScheduledTask -TaskName "Palawan Daily Migration"
```

**Or run the batch file directly:**
```cmd
cd c:\Users\Admin\Operation-Report-System
run_palawan_migration.bat
```

## Data Flow

### Before Migration
```
daily_reports (Brand B)
├─ palawan_sendout_principal: 100
├─ palawan_payout_principal: 50
├─ palawan_international_principal: 25
└─ palawan_suki_discounts: 5

daily_reports_brand_a (Brand A)
└─ [same structure as Brand B]

payable_tbl_brand_a
└─ [empty or only old data]
```

### After Migration
```
daily_reports (Brand B) - CLEARED
├─ palawan_sendout_principal: 0
├─ palawan_payout_principal: 0
├─ palawan_international_principal: 0
└─ palawan_suki_discounts: 0

daily_reports_brand_a (Brand A) - CLEARED
└─ [all zeroes]

payable_tbl_brand_a - POPULATED
├─ sendout_capital: 100
├─ payout_capital: 50
├─ international_capital: 25
└─ skid: 5
```

## Troubleshooting

### Task Not Running at 8:30 AM

1. Check if Task Scheduler service is running:
   ```powershell
   Get-Service -Name "TaskScheduler"
   ```

2. Verify task configuration:
   ```powershell
   Get-ScheduledTask -TaskName "Palawan Daily Migration" | Format-List
   ```

3. Check Windows Event Viewer for errors:
   - Event Viewer → Windows Logs → System
   - Filter by Task Scheduler

### Script Errors

1. Check the migration log file in the `logs/` directory
2. Look for any error messages at the end of the log
3. Ensure the database connection is working

### Database Connection Issues

The script uses the same database connection as the application (`api_db_manager`). If the script fails:
- Verify database credentials are correct
- Check if the database server is online
- Ensure network connectivity to the database

## Disabling or Removing the Task

### Disable the task (keep it, but don't run)
```powershell
Disable-ScheduledTask -TaskName "Palawan Daily Migration"
```

### Re-enable the task
```powershell
Enable-ScheduledTask -TaskName "Palawan Daily Migration"
```

### Remove the task completely
```powershell
Unregister-ScheduledTask -TaskName "Palawan Daily Migration" -Confirm:$false
```

## FAQ

**Q: What if the app is being used at 8:30 AM?**
A: The migration process only reads from `daily_reports` and inserts into `payable_tbl_brand_a`. It does not affect current user operations. However, it's recommended to run the migration during off-hours.

**Q: Will this affect live reports?**
A: No. The migration only moves data to `payable_tbl_brand_a`, which is the primary source for reports. Historical reports will now load data from `payable_tbl_brand_a` instead of the legacy tables.

**Q: Can I run the migration manually?**
A: Yes! Run the batch file directly:
```cmd
c:\Users\Admin\Operation-Report-System\run_palawan_migration.bat
```

**Q: What if a record fails to migrate?**
A: The script logs the error and continues with the next record. Failed records are NOT deleted from the source table, so they can be retried in the next run.

**Q: How often should I check the logs?**
A: Once a week is recommended to ensure migrations are running smoothly. You can also set up email notifications in Task Scheduler to alert you if the task fails.

**Q: Can I change the migration time?**
A: Yes! Edit the scheduled task in Task Scheduler and change the trigger time from 08:30 to your preferred time.

## Support

For issues or questions:
1. Check the migration logs in `logs/` directory
2. Verify the Task Scheduler configuration
3. Ensure database connectivity
4. Check Windows Event Viewer for system errors
