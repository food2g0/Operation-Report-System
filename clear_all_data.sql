-- Clear All Data SQL Script
-- This script removes all data from all tables while preserving table structures
-- Use this when preparing for production to remove test data

-- WARNING: This is a destructive operation!
-- Make sure you have a backup before running this script.

-- Disable foreign key checks to avoid constraint errors
SET FOREIGN_KEY_CHECKS = 0;

-- Clear all data from tables (in order to avoid FK constraints)
TRUNCATE TABLE daily_reports;
TRUNCATE TABLE users;
TRUNCATE TABLE branches;
TRUNCATE TABLE corporations;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Verify tables are empty
SELECT 'daily_reports' as table_name, COUNT(*) as row_count FROM daily_reports
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'branches', COUNT(*) FROM branches
UNION ALL
SELECT 'corporations', COUNT(*) FROM corporations;

-- All tables should show 0 rows
