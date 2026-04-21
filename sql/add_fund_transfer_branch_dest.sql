
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'daily_reports_brand_a' 
    AND COLUMN_NAME = 'fund_transfer_to_branch_dest');
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE daily_reports_brand_a ADD COLUMN fund_transfer_to_branch_dest VARCHAR(255) DEFAULT NULL', 
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- fund_transfer_to_branch_dest on daily_reports
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'daily_reports' 
    AND COLUMN_NAME = 'fund_transfer_to_branch_dest');
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE daily_reports ADD COLUMN fund_transfer_to_branch_dest VARCHAR(255) DEFAULT NULL', 
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- fund_transfer_from_branch_dest on daily_reports_brand_a
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'daily_reports_brand_a' 
    AND COLUMN_NAME = 'fund_transfer_from_branch_dest');
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE daily_reports_brand_a ADD COLUMN fund_transfer_from_branch_dest VARCHAR(255) DEFAULT NULL', 
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- fund_transfer_from_branch_dest on daily_reports
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'daily_reports' 
    AND COLUMN_NAME = 'fund_transfer_from_branch_dest');
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE daily_reports ADD COLUMN fund_transfer_from_branch_dest VARCHAR(255) DEFAULT NULL', 
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
