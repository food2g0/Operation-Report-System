#!/usr/bin/env python3
from db_connect_pooled import db_manager

# Query the report for RICHELLE TECSON group at KRUS NA LIGAS branch on March 19, 2026
query = """
SELECT date, branch, corporation, debit_total, credit_total FROM daily_reports_brand_a 
WHERE date = '2026-03-19'
  AND corporation = 'RICHELLE TECSON'
  AND branch = 'KRUS NA LIGAS'
LIMIT 1
"""

result = db_manager.execute_query(query)
if result:
    report = result[0]
    print("=" * 80)
    print("REPORT DATA - RICHELLE TECSON / KRUS NA LIGAS / 2026-03-19")
    print("=" * 80)
    print(f"Date:         {report['date']}")
    print(f"Branch:       {report['branch']}")
    print(f"Corporation:  {report['corporation']}")
    print(f"Debit Total:  {report['debit_total']}")
    print(f"Credit Total: {report['credit_total']}")
    
    print(f"\n⚠️  Expected debit total: 32980.00")
    print(f"⚠️  Actual debit total:   {report['debit_total']}")
    if report['debit_total'] != 32980.00:
        print(f"⚠️  DISCREPANCY: {float(report['debit_total']) - 32980.00:+.2f}")
else:
    print("Report not found!")
