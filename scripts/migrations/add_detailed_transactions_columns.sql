-- ============================================================================
-- Migration: Add Detailed Transaction Columns to payable_tbl_brand_a
-- ============================================================================
-- This script adds 9 new JSON columns to store detailed Palawan transactions
-- Each column stores a JSON array of transaction objects with all transaction details
--
-- Transaction object structure:
-- {
--   "code": "TX001",
--   "receiver": "John Doe",
--   "sender": "Jane Smith",
--   "principal": 5000.00,
--   "commission": 1000.00,
--   "sc": 500.00,
--   "total_sc": 1500.00,
--   "income": 430.00,
--   "ar_palawan": 5430.00,
--   "kyc_docs": "Valid ID",
--   "business_name": "ABC Company",
--   "relationship": "Friend",
--   "source_funds": "Salary",
--   "purpose": "Payment",
--   "evaluation": "Verified"
-- }
-- ============================================================================

-- Send-Out Detailed Transactions
ALTER TABLE payable_tbl_brand_a
ADD COLUMN IF NOT EXISTS sendout_detailed_principal LONGTEXT
COMMENT 'Send-Out Principal - JSON array of detailed transactions';

ALTER TABLE payable_tbl_brand_a
ADD COLUMN IF NOT EXISTS sendout_detailed_sc LONGTEXT
COMMENT 'Send-Out SC - JSON array of detailed transactions';

ALTER TABLE payable_tbl_brand_a
ADD COLUMN IF NOT EXISTS sendout_detailed_commission LONGTEXT
COMMENT 'Send-Out Commission - JSON array of detailed transactions';

-- Pay-Out Detailed Transactions
ALTER TABLE payable_tbl_brand_a
ADD COLUMN IF NOT EXISTS payout_detailed_principal LONGTEXT
COMMENT 'Pay-Out Principal - JSON array of detailed transactions';

ALTER TABLE payable_tbl_brand_a
ADD COLUMN IF NOT EXISTS payout_detailed_sc LONGTEXT
COMMENT 'Pay-Out SC - JSON array of detailed transactions';

ALTER TABLE payable_tbl_brand_a
ADD COLUMN IF NOT EXISTS payout_detailed_commission LONGTEXT
COMMENT 'Pay-Out Commission - JSON array of detailed transactions';

-- International Detailed Transactions
ALTER TABLE payable_tbl_brand_a
ADD COLUMN IF NOT EXISTS international_detailed_principal LONGTEXT
COMMENT 'International Principal - JSON array of detailed transactions';

ALTER TABLE payable_tbl_brand_a
ADD COLUMN IF NOT EXISTS international_detailed_sc LONGTEXT
COMMENT 'International SC - JSON array of detailed transactions';

ALTER TABLE payable_tbl_brand_a
ADD COLUMN IF NOT EXISTS international_detailed_commission LONGTEXT
COMMENT 'International Commission - JSON array of detailed transactions';

-- ============================================================================
-- Verification Query - Check if all columns were created
-- ============================================================================
-- Run this query after executing the above to verify all columns exist:
/*
SELECT COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'payable_tbl_brand_a'
AND COLUMN_NAME LIKE '%detailed%'
ORDER BY COLUMN_NAME;
*/
-- Expected result: 9 rows with LONGTEXT data type
