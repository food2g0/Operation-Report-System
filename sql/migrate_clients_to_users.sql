-- Migration Script: Remove clients table and migrate to users table
-- This script migrates client data from the clients table to the users table
-- and then drops the clients table.

-- Step 1: Add first_name and last_name columns to users table if they don't exist
-- Note: MySQL doesn't support IF NOT EXISTS for ALTER TABLE ADD COLUMN
-- Check if columns exist first, then run these manually if needed:

-- Add first_name column (run only if column doesn't exist)
-- Check with: SHOW COLUMNS FROM users LIKE 'first_name';
ALTER TABLE users ADD COLUMN first_name VARCHAR(255);

-- Add last_name column (run only if column doesn't exist)
-- Check with: SHOW COLUMNS FROM users LIKE 'last_name';
ALTER TABLE users ADD COLUMN last_name VARCHAR(255);

-- Step 2: Migrate existing client data from clients table to users table
-- This will insert clients that don't already exist in the users table
INSERT INTO users (username, password, first_name, last_name, corporation, branch, role, created_at)
SELECT 
    c.username,
    NULL as password,  -- Password will need to be reset by admin as clients used hashed passwords
    c.first_name,
    c.last_name,
    corp.name as corporation,
    b.name as branch,
    'user' as role,
    c.created_at
FROM clients c
LEFT JOIN corporations corp ON c.corporation_id = corp.id
LEFT JOIN branches b ON c.branch_id = b.id
WHERE NOT EXISTS (
    SELECT 1 FROM users u WHERE u.username = c.username
);

-- Step 3: Drop the clients table
DROP TABLE IF EXISTS clients;

-- Migration complete!
-- Note: Migrated clients will have NULL passwords and will need to have passwords reset by an administrator.
