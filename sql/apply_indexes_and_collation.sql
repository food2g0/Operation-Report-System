-- ============================================================================
-- Performance Optimization: Indexes + Collation Unification
-- Run this on your MySQL server to handle 600+ branches with thousands of reports.
--
-- Usage:  mysql -u root -p your_database < apply_indexes_and_collation.sql
-- ============================================================================

-- ──────────────────────────────────────────────────────────────────────────────
-- 1) UNIFY COLLATION — Makes JOINs use indexes instead of full table scans
-- ──────────────────────────────────────────────────────────────────────────────
ALTER TABLE daily_reports CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE daily_reports_brand_a CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE branches CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE corporations CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE payable_tbl CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE payable_tbl_brand_a CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE cash_float_tbl CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE daily_transaction_tbl_brand_a CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE other_services_tbl_brand_a CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE global_other_services_tbl CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE extra_space_fund_transfer CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

-- ──────────────────────────────────────────────────────────────────────────────
-- 2) ADD INDEXES — Composite indexes for the most common admin query patterns
--    Uses IF NOT EXISTS via stored procedure to avoid errors on re-run.
-- ──────────────────────────────────────────────────────────────────────────────

DELIMITER //
CREATE PROCEDURE IF NOT EXISTS add_index_if_not_exists(
    IN p_table VARCHAR(128),
    IN p_index VARCHAR(128),
    IN p_columns VARCHAR(512)
)
BEGIN
    DECLARE idx_exists INT DEFAULT 0;
    SELECT COUNT(*) INTO idx_exists
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = p_table
      AND INDEX_NAME = p_index;
    IF idx_exists = 0 THEN
        SET @sql = CONCAT('ALTER TABLE `', p_table, '` ADD INDEX `', p_index, '` (', p_columns, ')');
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END //
DELIMITER ;

-- daily_reports (Brand B)
CALL add_index_if_not_exists('daily_reports', 'idx_dr_corp_date', 'corporation, date');
CALL add_index_if_not_exists('daily_reports', 'idx_dr_branch_date', 'branch, date');
CALL add_index_if_not_exists('daily_reports', 'idx_dr_date', 'date');
CALL add_index_if_not_exists('daily_reports', 'idx_dr_corp_branch_date', 'corporation, branch, date');
CALL add_index_if_not_exists('daily_reports', 'idx_dr_variance', 'variance_status, corporation, date');

-- daily_reports_brand_a (Brand A)
CALL add_index_if_not_exists('daily_reports_brand_a', 'idx_dra_corp_date', 'corporation, date');
CALL add_index_if_not_exists('daily_reports_brand_a', 'idx_dra_branch_date', 'branch, date');
CALL add_index_if_not_exists('daily_reports_brand_a', 'idx_dra_date', 'date');
CALL add_index_if_not_exists('daily_reports_brand_a', 'idx_dra_corp_branch_date', 'corporation, branch, date');
CALL add_index_if_not_exists('daily_reports_brand_a', 'idx_dra_variance', 'variance_status, corporation, date');

-- branches
CALL add_index_if_not_exists('branches', 'idx_branches_name', 'name');
CALL add_index_if_not_exists('branches', 'idx_branches_os', 'os_name');
CALL add_index_if_not_exists('branches', 'idx_branches_global', 'global_tag');
CALL add_index_if_not_exists('branches', 'idx_branches_os_registered', 'os_name, is_registered');
CALL add_index_if_not_exists('branches', 'idx_branches_global_os', 'global_tag, os_name, is_registered');

-- payable tables (composite for LEFT JOIN on corporation + branch + date)
CALL add_index_if_not_exists('payable_tbl', 'idx_pay_corp_date', 'corporation, date');
CALL add_index_if_not_exists('payable_tbl', 'idx_pay_corp_branch_date', 'corporation, branch, date');
CALL add_index_if_not_exists('payable_tbl_brand_a', 'idx_paya_corp_date', 'corporation, date');
CALL add_index_if_not_exists('payable_tbl_brand_a', 'idx_paya_corp_branch_date', 'corporation, branch, date');

-- other service tables
CALL add_index_if_not_exists('daily_transaction_tbl_brand_a', 'idx_dt_corp_date', 'corporation, date');
CALL add_index_if_not_exists('other_services_tbl_brand_a', 'idx_os_corp_date', 'corporation, date');
CALL add_index_if_not_exists('global_other_services_tbl', 'idx_gos_branch_date', 'branch, date');
CALL add_index_if_not_exists('global_other_services_tbl', 'idx_gos_date', 'date');

-- cash_float_tbl
CALL add_index_if_not_exists('cash_float_tbl', 'idx_cf_branch_corp_date', 'branch, corporation, date');

-- extra_space_fund_transfer
CALL add_index_if_not_exists('extra_space_fund_transfer', 'idx_esft_date', 'report_date');

-- Clean up helper procedure
DROP PROCEDURE IF EXISTS add_index_if_not_exists;

-- ──────────────────────────────────────────────────────────────────────────────
-- 3) VERIFY — Quick check
-- ──────────────────────────────────────────────────────────────────────────────
SELECT TABLE_NAME, INDEX_NAME, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS columns
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN (
    'daily_reports', 'daily_reports_brand_a', 'branches', 'corporations',
    'payable_tbl', 'payable_tbl_brand_a', 'cash_float_tbl',
    'daily_transaction_tbl_brand_a', 'other_services_tbl_brand_a',
    'global_other_services_tbl', 'extra_space_fund_transfer'
  )
GROUP BY TABLE_NAME, INDEX_NAME
ORDER BY TABLE_NAME, INDEX_NAME;
