#!/usr/bin/env python3
from db_connect_pooled import db_manager

# Search for RICHELLE TECSON in Brand B (daily_reports)
print("=" * 80)
print("Searching for RICHELLE TECSON in Brand B (daily_reports):")
print("=" * 80)
query = "SELECT date, branch, debit_total, credit_total FROM daily_reports WHERE corporation = 'RICHELLE TECSON' AND date = '2026-03-19' LIMIT 10"
result = db_manager.execute_query(query)

if result:
    for row in result:
        print(f"Date: {row.get('date')} | Branch: {row.get('branch'):30s} | Debit: {row.get('debit_total', 0):12.2f} | Credit: {row.get('credit_total', 0):12.2f}")
else:
    print("No reports found. Let me search for any RICHELLE TECSON reports...")
    query2 = "SELECT date, branch, debit_total FROM daily_reports WHERE corporation LIKE '%RICHELLE%' LIMIT 10"
    result2 = db_manager.execute_query(query2)
    
    if result2:
        for row in result2:
            print(f"Date: {row.get('date')} | Branch: {row.get('branch'):30s} | Debit: {row.get('debit_total', 0):12.2f}")
    else:
        print("No RICHELLE TECSON found in daily_reports either")
        
        # List all corporations with reports on this date
        print("\n" + "=" * 80)
        print("Corporations with reports on 2026-03-19 (Brand B):")
        print("=" * 80)
        query3 = "SELECT DISTINCT corporation FROM daily_reports WHERE date = '2026-03-19' LIMIT 10"
        result3 = db_manager.execute_query(query3)
        if result3:
            for row in result3:
                print(f"  - {row.get('corporation')}")
