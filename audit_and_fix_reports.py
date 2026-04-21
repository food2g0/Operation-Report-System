#!/usr/bin/env python3
"""
AUDIT & FIX SCRIPT for calculation errors across all branches

CORRECT FORMULA:
- Total Cash Receipt (Debit) = Beginning Balance + Sum of all debit fields
- Total Cash Out (Credit) = Sum of all credit fields
- Ending Balance = Total Cash Receipt - Total Cash Out
"""
import json
from db_connect_pooled import db_manager

# Load field config
cfg_result = db_manager.execute_query('SELECT config_value FROM field_config WHERE config_key = "field_definitions" LIMIT 1')
if not cfg_result:
    print("ERROR: Could not load field config")
    exit(1)

cfg = json.loads(cfg_result[0]['config_value'])
debit_fields = cfg.get("Brand A", {}).get("debit", [])
credit_fields = cfg.get("Brand A", {}).get("credit", [])

# Get all DB column names for debit and credit
debit_cols = [f[2] for f in debit_fields if len(f) >= 3]
credit_cols = [f[2] for f in credit_fields if len(f) >= 3]

print("=" * 100)
print("AUDIT SCRIPT: Finding calculation errors in daily_reports_brand_a")
print("=" * 100)

# Query all reports and check their totals
query = "SELECT id, date, branch, corporation, beginning_balance, debit_total, credit_total, ending_balance FROM daily_reports_brand_a ORDER BY date DESC, branch"
all_reports = db_manager.execute_query(query)

if not all_reports:
    print("No reports found")
    exit(0)

discrepancies = []

for report in all_reports:
    report_id = report['id']
    date = report['date']
    branch = report['branch']
    corp = report['corporation']
    beginning = float(report['beginning_balance'])
    stored_debit = float(report['debit_total'])
    stored_credit = float(report['credit_total'])
    stored_ending = float(report['ending_balance'])
    
    # Get the actual data for this report
    data_query = "SELECT * FROM daily_reports_brand_a WHERE id = %s"
    data_result = db_manager.execute_query(data_query, (report_id,))
    
    if not data_result:
        continue
    
    data = data_result[0]
    
    # Calculate what the totals SHOULD be using CORRECT FORMULA:
    # Debit Total = Beginning Balance + Sum of debit fields
    # Credit Total = Sum of credit fields
    # Ending Balance = Debit Total - Credit Total
    debit_field_sum = sum(float(data.get(col, 0)) for col in debit_cols if col in data and data[col])
    credit_field_sum = sum(float(data.get(col, 0)) for col in credit_cols if col in data and data[col])
    
    calculated_debit = beginning + debit_field_sum
    calculated_credit = credit_field_sum
    calculated_ending = calculated_debit - calculated_credit
    
    # Check for discrepancies
    debit_diff = abs(stored_debit - calculated_debit)
    credit_diff = abs(stored_credit - calculated_credit)
    ending_diff = abs(stored_ending - calculated_ending)
    
    if debit_diff > 0.01 or credit_diff > 0.01 or ending_diff > 0.01:
        discrepancies.append({
            'id': report_id,
            'date': date,
            'branch': branch,
            'corp': corp,
            'beginning': beginning,
            'debit_issue': (stored_debit, calculated_debit, debit_diff) if debit_diff > 0.01 else None,
            'credit_issue': (stored_credit, calculated_credit, credit_diff) if credit_diff > 0.01 else None,
            'ending_issue': (stored_ending, calculated_ending, ending_diff) if ending_diff > 0.01 else None,
        })

print(f"\nFound {len(discrepancies)} reports with calculation errors:\n")

if discrepancies:
    print(f"{'Date':<12} {'Branch':<30} {'Issue':<60} {'Diff':<10}")
    print("-" * 115)
    
    for disc in discrepancies:
        issue_str = ""
        diff_str = ""
        
        if disc['debit_issue']:
            stored, calc, diff = disc['debit_issue']
            issue_str += f"Debit: {stored:.2f} → {calc:.2f}"
            diff_str = f"{diff:+.2f}"
        
        if disc['credit_issue']:
            if issue_str:
                issue_str += " | "
            stored, calc, diff = disc['credit_issue']
            issue_str += f"Credit: {stored:.2f} → {calc:.2f}"
            diff_str = f"{diff:+.2f}"
        
        if disc['ending_issue']:
            if issue_str:
                issue_str += " | "
            stored, calc, diff = disc['ending_issue']
            issue_str += f"Ending: {stored:.2f} → {calc:.2f}"
            diff_str = f"{diff:+.2f}"
        
        print(f"{str(disc['date']):<12} {disc['branch']:<30} {issue_str:<60} {diff_str:<10}")

print("\n" + "=" * 100)
print(f"SUMMARY: {len(discrepancies)} reports need fixing\n")

if discrepancies:
    # Ask user if they want to fix them
    response = input("Do you want to automatically fix these discrepancies? (yes/no): ").strip().lower()
    
    if response == 'yes':
        fixed_count = 0
        for disc in discrepancies:
            fixes = []
            
            if disc['debit_issue']:
                stored, calc, diff = disc['debit_issue']
                db_manager.execute_query(
                    "UPDATE daily_reports_brand_a SET debit_total = %s WHERE id = %s",
                    (calc, disc['id'])
                )
                fixes.append(f"Debit: {stored:.2f} → {calc:.2f}")
                fixed_count += 1
            
            if disc['credit_issue']:
                stored, calc, diff = disc['credit_issue']
                db_manager.execute_query(
                    "UPDATE daily_reports_brand_a SET credit_total = %s WHERE id = %s",
                    (calc, disc['id'])
                )
                fixes.append(f"Credit: {stored:.2f} → {calc:.2f}")
                fixed_count += 1
            
            if disc['ending_issue']:
                stored, calc, diff = disc['ending_issue']
                db_manager.execute_query(
                    "UPDATE daily_reports_brand_a SET ending_balance = %s WHERE id = %s",
                    (calc, disc['id'])
                )
                fixes.append(f"Ending: {stored:.2f} → {calc:.2f}")
                fixed_count += 1
        
        print(f"\n✓ Fixed {fixed_count} calculation errors!")
    else:
        print("No changes made.")
else:
    print("✓ All reports are correct! No discrepancies found.")
