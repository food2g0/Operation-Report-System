-- db_optimizations.sql
-- Indexes, optional partitioning, and summary table for daily_reports
-- Run: mysql -u root -p operation_db < db_optimizations.sql

-- 1) Important Indexes (create only those you need based on query patterns)
ALTER TABLE daily_reports
  ADD INDEX idx_reports_corp_branch_date (corporation, branch, date),
  ADD INDEX idx_reports_date (date),
  ADD INDEX idx_reports_username (username),
  ADD INDEX idx_reports_mc_entries_count (mc_entries_count);

-- Add any additional selective indexes used by admin filters, e.g.:
-- ALTER TABLE daily_reports ADD INDEX idx_reports_cash_result (cash_result);

-- 2) Optional: Partition by RANGE on YEAR(date)
-- NOTE: MySQL partitioning has operational considerations (ALTERs can be heavy).
-- Uncomment and adapt partitions to your retention policy before running.
-- ALTER TABLE daily_reports
-- PARTITION BY RANGE (YEAR(`date`)) (
--   PARTITION p2023 VALUES LESS THAN (2024),
--   PARTITION p2024 VALUES LESS THAN (2025),
--   PARTITION p2025 VALUES LESS THAN (2026),
--   PARTITION pmax VALUES LESS THAN (MAXVALUE)
-- );

-- 3) Materialized summary table for fast admin reporting
CREATE TABLE IF NOT EXISTS daily_reports_summary (
  summary_date DATE NOT NULL,
  corporation VARCHAR(255),
  branch VARCHAR(255),
  total_reports INT DEFAULT 0,
  sum_debit_total DECIMAL(22,2) DEFAULT 0.00,
  sum_credit_total DECIMAL(22,2) DEFAULT 0.00,
  avg_cash_result DECIMAL(22,2) DEFAULT 0.00,
  PRIMARY KEY (summary_date, corporation, branch)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Populate (initial load)
INSERT INTO daily_reports_summary (summary_date, corporation, branch, total_reports, sum_debit_total, sum_credit_total, avg_cash_result)
SELECT
  `date` AS summary_date,
  corporation,
  branch,
  COUNT(*) AS total_reports,
  SUM(debit_total) AS sum_debit_total,
  SUM(credit_total) AS sum_credit_total,
  AVG(cash_result) AS avg_cash_result
FROM daily_reports
GROUP BY `date`, corporation, branch
ON DUPLICATE KEY UPDATE
  total_reports = VALUES(total_reports),
  sum_debit_total = VALUES(sum_debit_total),
  sum_credit_total = VALUES(sum_credit_total),
  avg_cash_result = VALUES(avg_cash_result);

-- 4) Example maintenance: refresh a single date's summary
-- CALL this after bulk inserts for a date or run nightly.
-- REPLACE INTO daily_reports_summary (summary_date, corporation, branch, total_reports, sum_debit_total, sum_credit_total, avg_cash_result)
-- SELECT `date`, corporation, branch, COUNT(*), SUM(debit_total), SUM(credit_total), AVG(cash_result) FROM daily_reports
-- WHERE `date` = '2026-02-10' GROUP BY `date`, corporation, branch;

-- 5) Optional MySQL Event (automated daily refresh) - enable event_scheduler first
-- SET GLOBAL event_scheduler = ON;
-- CREATE EVENT IF NOT EXISTS ev_refresh_daily_reports_summary
-- ON SCHEDULE EVERY 1 DAY STARTS (CURRENT_DATE + INTERVAL 1 DAY)
-- DO
-- BEGIN
--   REPLACE INTO daily_reports_summary (summary_date, corporation, branch, total_reports, sum_debit_total, sum_credit_total, avg_cash_result)
--   SELECT `date`, corporation, branch, COUNT(*), SUM(debit_total), SUM(credit_total), AVG(cash_result)
--   FROM daily_reports
--   WHERE `date` >= CURDATE() - INTERVAL 30 DAY
--   GROUP BY `date`, corporation, branch;
-- END;

-- 6) Query examples using the summary table
-- Fast overall daily totals for a corporation
-- SELECT summary_date, total_reports, sum_debit_total, sum_credit_total FROM daily_reports_summary WHERE corporation = 'CorpName' ORDER BY summary_date DESC LIMIT 30;

-- Fast filtering on active table (use selective indexes)
-- SELECT date, username, branch, beginning_balance, ending_balance FROM daily_reports
-- WHERE corporation='CorpName' AND branch='BranchA' AND date BETWEEN '2026-01-01' AND '2026-01-31'
-- ORDER BY date DESC LIMIT 100;

-- End of file
