-- Add empeno_motor_car_breakdown column to daily_reports and daily_reports_brand_a
ALTER TABLE daily_reports ADD COLUMN IF NOT EXISTS empeno_motor_car_breakdown TEXT DEFAULT NULL;
ALTER TABLE daily_reports_brand_a ADD COLUMN IF NOT EXISTS empeno_motor_car_breakdown TEXT DEFAULT NULL;
