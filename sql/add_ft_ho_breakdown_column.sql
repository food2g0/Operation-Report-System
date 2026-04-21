-- Add ft_ho_breakdown column to daily_reports and daily_reports_brand_a
-- Stores JSON array of [bank_display, bank_id, amount] for each fund transfer
ALTER TABLE daily_reports ADD COLUMN ft_ho_breakdown TEXT DEFAULT NULL;
ALTER TABLE daily_reports_brand_a ADD COLUMN ft_ho_breakdown TEXT DEFAULT NULL;
