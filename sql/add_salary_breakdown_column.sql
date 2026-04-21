-- Migration: Add pc_salary_breakdown column to daily_reports_brand_a
-- This column stores the employee salary breakdown as JSON for Brand A reports

ALTER TABLE daily_reports_brand_a 
ADD COLUMN IF NOT EXISTS pc_salary_breakdown TEXT DEFAULT NULL;
