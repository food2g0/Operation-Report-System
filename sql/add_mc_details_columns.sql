ALTER TABLE daily_reports ADD COLUMN IF NOT EXISTS mc_in_details TEXT;
ALTER TABLE daily_reports ADD COLUMN IF NOT EXISTS mc_out_details TEXT;
ALTER TABLE daily_reports_brand_a ADD COLUMN IF NOT EXISTS mc_in_details TEXT;
ALTER TABLE daily_reports_brand_a ADD COLUMN IF NOT EXISTS mc_out_details TEXT;
