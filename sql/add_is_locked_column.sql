-- Migration: Add is_locked column to daily_reports and daily_reports_brand_a
-- This column controls whether a submitted entry can be edited by the client.
-- is_locked = 1 (default): Entry is submitted, client cannot edit
-- is_locked = 0: Entry has been reset by admin, client can edit and resubmit

-- Brand B table
ALTER TABLE daily_reports
    ADD COLUMN IF NOT EXISTS is_locked TINYINT(1) NOT NULL DEFAULT 1;

-- Brand A table
ALTER TABLE daily_reports_brand_a
    ADD COLUMN IF NOT EXISTS is_locked TINYINT(1) NOT NULL DEFAULT 1;
