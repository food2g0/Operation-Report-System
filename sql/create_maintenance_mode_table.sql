-- Migration: Create maintenance_mode table
-- This table stores system-wide maintenance mode status

CREATE TABLE IF NOT EXISTS maintenance_mode (
    id INT AUTO_INCREMENT PRIMARY KEY,
    is_active BOOLEAN DEFAULT FALSE,
    title VARCHAR(255) DEFAULT 'System Maintenance',
    message TEXT,
    started_at DATETIME,
    ends_at DATETIME,
    started_by VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
