-- Create currencies table for centralized MC currency management
-- This allows SuperAdmins to add/remove currencies without updating client code

CREATE TABLE IF NOT EXISTS currencies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    currency_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert default currencies if table is empty
INSERT IGNORE INTO currencies (currency_name, description, is_active) VALUES
('USD - US Dollar', 'United States Dollar', TRUE),
('EUR - Euro', 'European Union Euro', TRUE),
('JPY - Japanese Yen', 'Japanese Yen', TRUE),
('KRW - Korean Won', 'South Korean Won', TRUE),
('CNY - Chinese Yuan', 'Chinese Yuan Renminbi', TRUE),
('SGD - Singapore Dollar', 'Singapore Dollar', TRUE),
('AED - UAE Dirham', 'United Arab Emirates Dirham', TRUE),
('SAR - Saudi Riyal', 'Saudi Arabian Riyal', TRUE),
('AUD - Australian Dollar', 'Australian Dollar', TRUE),
('CAD - Canadian Dollar', 'Canadian Dollar', TRUE),
('GBP - British Pound', 'British Pound Sterling', TRUE),
('HKD - Hong Kong Dollar', 'Hong Kong Dollar', TRUE),
('CHF - Swiss Franc', 'Swiss Franc', TRUE),
('NOK - Norwegian Krone', 'Norwegian Krone', TRUE),
('SEK - Swedish Krona', 'Swedish Krona', TRUE),
('THB - Thai Baht', 'Thai Baht', TRUE),
('MYR - Malaysian Ringgit', 'Malaysian Ringgit', TRUE),
('IDR - Indonesian Rupiah', 'Indonesian Rupiah', TRUE),
('VND - Vietnamese Dong', 'Vietnamese Dong', TRUE),
('TWD - Taiwan Dollar', 'Taiwan Dollar', TRUE);
