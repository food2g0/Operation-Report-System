-- Add sub_corporation_id column to branches table
ALTER TABLE branches ADD COLUMN sub_corporation_id INT DEFAULT NULL;

-- Optional: Add foreign key constraint if you want to enforce referential integrity
-- ALTER TABLE branches ADD CONSTRAINT fk_sub_corp FOREIGN KEY (sub_corporation_id) REFERENCES corporations(id) ON DELETE SET NULL;
