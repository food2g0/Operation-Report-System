-- Add missing columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(255) AFTER password;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(255) AFTER first_name;
ALTER TABLE users ADD COLUMN IF NOT EXISTS corporation VARCHAR(255) AFTER last_name;
ALTER TABLE users ADD COLUMN IF NOT EXISTS branch VARCHAR(255) AFTER corporation;
