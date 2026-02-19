-- ================================================================
-- Create payable_tbl table for storing Palawan transaction data
-- ================================================================

CREATE TABLE IF NOT EXISTS `payable_tbl` (
    -- Primary key
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Identification fields
    `corporation` VARCHAR(255) NOT NULL,
    `branch` VARCHAR(255) NOT NULL,
    `date` DATE NOT NULL,
    
    -- Palawan Send-Out fields
    `sendout_capital` DECIMAL(15, 2) DEFAULT 0.00,
    `sendout_sc` DECIMAL(15, 2) DEFAULT 0.00,
    `sendout_commission` DECIMAL(15, 2) DEFAULT 0.00,
    `sendout_total` DECIMAL(15, 2) DEFAULT 0.00,
    
    -- Palawan Pay-Out fields
    `payout_capital` DECIMAL(15, 2) DEFAULT 0.00,
    `payout_sc` DECIMAL(15, 2) DEFAULT 0.00,
    `payout_commission` DECIMAL(15, 2) DEFAULT 0.00,
    `payout_total` DECIMAL(15, 2) DEFAULT 0.00,
    
    -- Palawan International fields
    `international_capital` DECIMAL(15, 2) DEFAULT 0.00,
    `international_sc` DECIMAL(15, 2) DEFAULT 0.00,
    `international_commission` DECIMAL(15, 2) DEFAULT 0.00,
    `international_total` DECIMAL(15, 2) DEFAULT 0.00,
    
    -- Adjustment fields (editable in the UI)
    `skid` DECIMAL(15, 2) DEFAULT 0.00 COMMENT 'Suki Discount',
    `skir` DECIMAL(15, 2) DEFAULT 0.00 COMMENT 'Suki Rebate',
    `cancellation` DECIMAL(15, 2) DEFAULT 0.00 COMMENT 'Cancellation amount',
    `inc` DECIMAL(15, 2) DEFAULT 0.00 COMMENT 'Incentive',
    
    -- Timestamps
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Unique constraint to prevent duplicate entries for same corporation/branch/date
    UNIQUE KEY `unique_payable_entry` (`corporation`, `branch`, `date`),
    
    -- Indexes for better query performance
    INDEX `idx_corporation` (`corporation`),
    INDEX `idx_branch` (`branch`),
    INDEX `idx_date` (`date`),
    INDEX `idx_corp_date` (`corporation`, `date`)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Stores Palawan transaction payables data';

-- ================================================================
-- Add some useful comments to the table
-- ================================================================

-- Optional: Add check constraints (MySQL 8.0.16+)
-- ALTER TABLE payable_tbl 
--     ADD CONSTRAINT chk_sendout_total CHECK (sendout_total >= 0),
--     ADD CONSTRAINT chk_payout_total CHECK (payout_total >= 0),
--     ADD CONSTRAINT chk_international_total CHECK (international_total >= 0);

-- ================================================================
-- Sample query to verify table creation
-- ================================================================

-- Check if table exists
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    CREATE_TIME,
    TABLE_COMMENT
FROM 
    INFORMATION_SCHEMA.TABLES
WHERE 
    TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'payable_tbl';

-- Show table structure
DESCRIBE payable_tbl;

-- ================================================================
-- Sample insert query (for testing purposes)
-- ================================================================

-- INSERT INTO payable_tbl 
--     (corporation, branch, date, 
--      sendout_capital, sendout_sc, sendout_commission, sendout_total,
--      payout_capital, payout_sc, payout_commission, payout_total,
--      international_capital, international_sc, international_commission, international_total,
--      skid, skir, cancellation, inc)
-- VALUES 
--     ('Sample Corp', 'Main Branch', '2024-02-11',
--      1000.00, 50.00, 25.00, 1075.00,
--      2000.00, 100.00, 50.00, 2150.00,
--      500.00, 25.00, 12.50, 537.50,
--      10.00, 5.00, 0.00, 15.00);

-- ================================================================
-- Useful queries for maintenance
-- ================================================================

-- Count records by corporation
-- SELECT corporation, COUNT(*) as record_count 
-- FROM payable_tbl 
-- GROUP BY corporation 
-- ORDER BY record_count DESC;

-- Get records for a specific date range
-- SELECT * FROM payable_tbl 
-- WHERE date BETWEEN '2024-01-01' AND '2024-12-31'
-- ORDER BY corporation, branch, date;

-- Calculate totals for a specific corporation and date
-- SELECT 
--     corporation,
--     date,
--     SUM(sendout_total) as total_sendout,
--     SUM(payout_total) as total_payout,
--     SUM(international_total) as total_international,
--     SUM(skid + skir + cancellation + inc) as total_adjustments
-- FROM payable_tbl
-- WHERE corporation = 'Your Corporation'
--   AND date = '2024-02-11'
-- GROUP BY corporation, date;