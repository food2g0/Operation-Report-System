-- Add fund_transfer_bank_account column to daily_reports tables
-- This stores the ID of the bank account selected by client for Fund Transfer to HEAD OFFICE

ALTER TABLE daily_reports_brand_a 
ADD COLUMN IF NOT EXISTS fund_transfer_bank_account INT DEFAULT NULL;

ALTER TABLE daily_reports 
ADD COLUMN IF NOT EXISTS fund_transfer_bank_account INT DEFAULT NULL;
