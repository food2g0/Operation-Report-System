-- ============================================================================
-- Add Detailed Transaction Columns ONE AT A TIME
-- ============================================================================
-- Run each ALTER TABLE statement separately in your MySQL client.
-- Do NOT run them all at once - they will time out or be interrupted.
-- Wait for each one to complete before running the next.
-- ============================================================================

-- 1. Send-Out Principal Details
ALTER TABLE payable_tbl_brand_a ADD COLUMN sendout_detailed_principal LONGTEXT COMMENT 'Send-Out Principal - JSON array';
-- Wait for completion before next statement

-- 2. Send-Out SC Details
ALTER TABLE payable_tbl_brand_a ADD COLUMN sendout_detailed_sc LONGTEXT COMMENT 'Send-Out SC - JSON array';

-- 3. Send-Out Commission Details
ALTER TABLE payable_tbl_brand_a ADD COLUMN sendout_detailed_commission LONGTEXT COMMENT 'Send-Out Commission - JSON array';

-- 4. Pay-Out Principal Details
ALTER TABLE payable_tbl_brand_a ADD COLUMN payout_detailed_principal LONGTEXT COMMENT 'Pay-Out Principal - JSON array';

-- 5. Pay-Out SC Details
ALTER TABLE payable_tbl_brand_a ADD COLUMN payout_detailed_sc LONGTEXT COMMENT 'Pay-Out SC - JSON array';

-- 6. Pay-Out Commission Details
ALTER TABLE payable_tbl_brand_a ADD COLUMN payout_detailed_commission LONGTEXT COMMENT 'Pay-Out Commission - JSON array';

-- 7. International Principal Details
ALTER TABLE payable_tbl_brand_a ADD COLUMN international_detailed_principal LONGTEXT COMMENT 'International Principal - JSON array';

-- 8. International SC Details
ALTER TABLE payable_tbl_brand_a ADD COLUMN international_detailed_sc LONGTEXT COMMENT 'International SC - JSON array';

-- 9. International Commission Details
ALTER TABLE payable_tbl_brand_a ADD COLUMN international_detailed_commission LONGTEXT COMMENT 'International Commission - JSON array';

-- ============================================================================
-- After all columns are added, verify with this query:
-- ============================================================================
SELECT COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'payable_tbl_brand_a'
AND COLUMN_NAME LIKE '%detailed%'
ORDER BY COLUMN_NAME;

-- Expected result: 9 rows with LONGTEXT data type
