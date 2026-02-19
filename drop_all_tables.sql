-- ============================================
-- CLEAR ALL DATA (TRUNCATE TABLES)
-- This removes all data but keeps table structures
-- ============================================

-- Disable foreign key checks
SET FOREIGN_KEY_CHECKS = 0;

-- Clear data from all tables (keeps structure)
TRUNCATE TABLE `daily_reports_summary`;
TRUNCATE TABLE `payable_tbl`;
TRUNCATE TABLE `daily_reports_brand_a`;
TRUNCATE TABLE `daily_reports`;
TRUNCATE TABLE `users`;
TRUNCATE TABLE `branches`;
TRUNCATE TABLE `corporations`;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Verify tables still exist (should show table names)
SHOW TABLES;
