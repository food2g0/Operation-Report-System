-- Add Empeno JEW breakdown columns so dialog row data survives posting/reload
ALTER TABLE daily_reports           ADD COLUMN IF NOT EXISTS empeno_jew_new_breakdown   TEXT DEFAULT NULL;
ALTER TABLE daily_reports           ADD COLUMN IF NOT EXISTS empeno_jew_renew_breakdown  TEXT DEFAULT NULL;
ALTER TABLE daily_reports_brand_a   ADD COLUMN IF NOT EXISTS empeno_jew_new_breakdown   TEXT DEFAULT NULL;
ALTER TABLE daily_reports_brand_a   ADD COLUMN IF NOT EXISTS empeno_jew_renew_breakdown  TEXT DEFAULT NULL;
