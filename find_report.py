#!/usr/bin/env python3
from db_connect_pooled import db_manager

# First, let's find all reports for the given date
query1 = "SELECT DISTINCT corporation, branch, debit_total FROM daily_reports_brand_a WHERE date = '2026-03-19' LIMIT 20"
result1 = db_manager.execute_query(query1)

print("=" * 80)
print("All reports on 2026-03-19 (Brand A):")
print("=" * 80)
if result1:
    for row in result1:
        print(f"Corporation: {row.get('corporation'):30s} | Branch: {row.get('branch'):30s} | Debit: {row.get('debit_total', 0)}")
else:
    print("No reports found for this date")

# Search for RICHELLE TECSON reports
print("\n" + "=" * 80)
print("All reports for RICHELLE TECSON (any date, Brand A):")
print("=" * 80)
query2 = "SELECT date, branch, debit_total, credit_total FROM daily_reports_brand_a WHERE corporation = 'RICHELLE TECSON' LIMIT 20"
result2 = db_manager.execute_query(query2)

if result2:
    for row in result2:
        print(f"Date: {row.get('date')} | Branch: {row.get('branch'):30s} | Debit: {row.get('debit_total', 0):12.2f} | Credit: {row.get('credit_total', 0):12.2f}")
else:
    print("No reports found for RICHELLE TECSON")
