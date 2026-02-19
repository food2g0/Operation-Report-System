from db_connect import db_manager

# Refresh summary for last N days (default 30)
import sys
n = int(sys.argv[1]) if len(sys.argv) > 1 else 30

q = f"REPLACE INTO daily_reports_summary (summary_date, corporation, branch, total_reports, sum_debit_total, sum_credit_total, avg_cash_result) SELECT `date`, corporation, branch, COUNT(*), SUM(debit_total), SUM(credit_total), AVG(cash_result) FROM daily_reports WHERE `date` >= CURDATE() - INTERVAL {n} DAY GROUP BY `date`, corporation, branch"
print('Running summary refresh for last', n, 'days')
res = db_manager.execute_query(q)
print('Result:', res)
