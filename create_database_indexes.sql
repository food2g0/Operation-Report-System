-- Database Indexes for Performance Optimization
-- Run this script to significantly improve query performance with large datasets
--
-- Expected improvement: 50-100x faster queries
-- Execution time: 2-5 minutes (depending on table size)

-- ============================================================================
-- PHASE 1: CRITICAL INDEXES (Most Important)
-- ============================================================================
-- These are the most frequently used query patterns

ALTER TABLE daily_reports ADD INDEX idx_date_branch (date, branch);
ALTER TABLE daily_reports_brand_a ADD INDEX idx_date_branch (date, branch);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_date_branch (date, branch);

-- ============================================================================
-- PHASE 2: COMMON FILTER INDEXES
-- ============================================================================
-- Used in most report queries

ALTER TABLE daily_reports ADD INDEX idx_corporation_date (corporation, date);
ALTER TABLE daily_reports_brand_a ADD INDEX idx_corporation_date (corporation, date);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_corporation_date (corporation, date);

-- ============================================================================
-- PHASE 3: INDIVIDUAL COLUMN INDEXES
-- ============================================================================
-- For searches by single column

ALTER TABLE daily_reports ADD INDEX idx_branch (branch);
ALTER TABLE daily_reports ADD INDEX idx_status (status);
ALTER TABLE daily_reports ADD INDEX idx_corporation (corporation);

ALTER TABLE daily_reports_brand_a ADD INDEX idx_branch (branch);
ALTER TABLE daily_reports_brand_a ADD INDEX idx_corporation (corporation);

ALTER TABLE payable_tbl_brand_a ADD INDEX idx_branch (branch);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_corporation (corporation);

-- ============================================================================
-- PHASE 4: SPECIALIZED INDEXES
-- ============================================================================
-- For specific query patterns (palawan data, aggregates, etc.)

ALTER TABLE payable_tbl_brand_a ADD INDEX idx_sendout_capital (sendout_capital);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_payout_capital (payout_capital);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_international_capital (international_capital);

ALTER TABLE daily_reports ADD INDEX idx_palawan_sendout (palawan_sendout_principal);
ALTER TABLE daily_reports ADD INDEX idx_palawan_payout (palawan_payout_principal);

-- ============================================================================
-- UPDATE TABLE STATISTICS
-- ============================================================================
-- Tells MySQL optimizer about table structure for better query planning

ANALYZE TABLE daily_reports;
ANALYZE TABLE daily_reports_brand_a;
ANALYZE TABLE payable_tbl_brand_a;

-- ============================================================================
-- VERIFY INDEXES WERE CREATED
-- ============================================================================
-- Check that all indexes are present

SELECT
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    SEQ_IN_INDEX,
    CARDINALITY
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = 'operation_report_system'
AND TABLE_NAME IN ('daily_reports', 'daily_reports_brand_a', 'payable_tbl_brand_a')
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;

-- ============================================================================
-- CHECK TABLE SIZES
-- ============================================================================

SELECT
    TABLE_NAME,
    ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) AS `Size_MB`,
    ROUND((DATA_LENGTH / 1024 / 1024), 2) AS `Data_MB`,
    ROUND((INDEX_LENGTH / 1024 / 1024), 2) AS `Index_MB`
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'operation_report_system'
AND TABLE_NAME IN ('daily_reports', 'daily_reports_brand_a', 'payable_tbl_brand_a')
ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC;
