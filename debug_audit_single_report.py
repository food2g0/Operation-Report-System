#!/usr/bin/env python3
"""
DEBUG SCRIPT: Analyze a single report to see exactly how calculations are being done
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

print("=" * 120)
print("FIELD CONFIG LOADED")
print("=" * 120)
print(f"\nDebit Fields ({len(debit_fields)}):")
for i, f in enumerate(debit_fields, 1):
    print(f"  {i:2d}. {f[0]:<40} -> {f[2] if len(f) >= 3 else 'NO DB COLUMN'}")

print(f"\nCredit Fields ({len(credit_fields)}):")
for i, f in enumerate(credit_fields, 1):
    print(f"  {i:2d}. {f[0]:<40} -> {f[2] if len(f) >= 3 else 'NO DB COLUMN'}")

# Get list of recent reports to debug
print("\n" + "=" * 120)
print("RECENT REPORTS (Pick one to debug)")
print("=" * 120)
query = "SELECT id, date, branch, corporation, beginning_balance, debit_total, credit_total, ending_balance FROM daily_reports_brand_a ORDER BY date DESC LIMIT 10"
recent = db_manager.execute_query(query)

for i, r in enumerate(recent, 1):
    print(f"{i}. ID={r['id']} | {r['date']} | {r['branch']:<30} | Corp={r['corporation']:<20} | Debit={r['debit_total']:>10.2f} | Credit={r['credit_total']:>10.2f}")

# Ask user which one to debug
report_num = input("\nEnter number (1-10) of report to debug, or 'id' to specify ID: ").strip()

if report_num.isdigit():
    report_id = recent[int(report_num) - 1]['id']
else:
    report_id = int(report_num)

# Get the full report data
data_query = "SELECT * FROM daily_reports_brand_a WHERE id = %s"
data_result = db_manager.execute_query(data_query, (report_id,))

if not data_result:
    print("Report not found")
    exit(1)

data = data_result[0]
print("\n" + "=" * 120)
print(f"ANALYZING REPORT ID: {report_id}")
print("=" * 120)

beginning = float(data['beginning_balance'])
stored_debit = float(data['debit_total'])
stored_credit = float(data['credit_total'])
stored_ending = float(data['ending_balance'])

print(f"\nStored Values in Database:")
print(f"  Beginning Balance: {beginning:>15.2f}")
print(f"  Debit Total:      {stored_debit:>15.2f}")
print(f"  Credit Total:     {stored_credit:>15.2f}")
print(f"  Ending Balance:   {stored_ending:>15.2f}")

# Calculate what the values SHOULD be
debit_cols = [f[2] for f in debit_fields if len(f) >= 3]
credit_cols = [f[2] for f in credit_fields if len(f) >= 3]

print(f"\n" + "=" * 120)
print("DEBIT FIELD VALUES")
print("=" * 120)
debit_field_sum = 0
for field_idx, (col, field_def) in enumerate(zip(debit_cols, debit_fields), 1):
    val = float(data.get(col, 0)) if data.get(col) else 0
    debit_field_sum += val
    if val != 0:
        print(f"{field_idx:2d}. {field_def[0]:<40} ({col:<30}) = {val:>12.2f}")

print(f"\nDebit Field Sum (all non-zero): {debit_field_sum:>12.2f}")
calculated_debit = beginning + debit_field_sum
print(f"Calculated Debit Total (Beginning + Sum): {calculated_debit:>12.2f}")
print(f"Stored Debit Total: {stored_debit:>12.2f}")
print(f"Difference: {abs(stored_debit - calculated_debit):>12.2f}")

print(f"\n" + "=" * 120)
print("CREDIT FIELD VALUES")
print("=" * 120)
credit_field_sum = 0
for field_idx, (col, field_def) in enumerate(zip(credit_cols, credit_fields), 1):
    val = float(data.get(col, 0)) if data.get(col) else 0
    credit_field_sum += val
    if val != 0:
        print(f"{field_idx:2d}. {field_def[0]:<40} ({col:<30}) = {val:>12.2f}")

print(f"\nCredit Field Sum (all non-zero): {credit_field_sum:>12.2f}")
calculated_credit = credit_field_sum
print(f"Calculated Credit Total: {calculated_credit:>12.2f}")
print(f"Stored Credit Total: {stored_credit:>12.2f}")
print(f"Difference: {abs(stored_credit - calculated_credit):>12.2f}")

print(f"\n" + "=" * 120)
print("ENDING BALANCE VERIFICATION")
print("=" * 120)
calculated_ending = calculated_debit - calculated_credit
print(f"Calculated: {calculated_debit:>12.2f} - {calculated_credit:>12.2f} = {calculated_ending:>12.2f}")
print(f"Stored:     {stored_ending:>12.2f}")
print(f"Difference: {abs(stored_ending - calculated_ending):>12.2f}")

print(f"\n" + "=" * 120)
print("SUMMARY")
print("=" * 120)
if abs(stored_debit - calculated_debit) > 0.01:
    print(f"❌ DEBIT MISMATCH: Stored={stored_debit:.2f} vs Calculated={calculated_debit:.2f} (Diff: {stored_debit - calculated_debit:+.2f})")
else:
    print(f"✅ Debit matches!")

if abs(stored_credit - calculated_credit) > 0.01:
    print(f"❌ CREDIT MISMATCH: Stored={stored_credit:.2f} vs Calculated={calculated_credit:.2f} (Diff: {stored_credit - calculated_credit:+.2f})")
else:
    print(f"✅ Credit matches!")

if abs(stored_ending - calculated_ending) > 0.01:
    print(f"❌ ENDING MISMATCH: Stored={stored_ending:.2f} vs Calculated={calculated_ending:.2f} (Diff: {stored_ending - calculated_ending:+.2f})")
else:
    print(f"✅ Ending balance matches!")
