#!/usr/bin/env python3
import json
from db_connect_pooled import db_manager

# Get field config
cfg_result = db_manager.execute_query('SELECT config_value FROM field_config WHERE config_key = "field_definitions" LIMIT 1')
if cfg_result:
    cfg = json.loads(cfg_result[0]['config_value'])
    credit_fields = cfg.get("Brand A", {}).get("credit", [])
    
    print("=" * 80)
    print("CREDIT FIELDS IN BRAND A:")
    print("=" * 80)
    for field in credit_fields:
        label = field[0]
        db_col = field[2] if len(field) >= 3 else None
        print(f"{label:40s} => {db_col}")
else:
    print("Could not load field config")

# Now get the actual data and calculate the total
print("\n" + "=" * 80)
print("ACTUAL VALUES FROM REPORT (CL-0042 / KRUS NA LIGAS / 2026-03-19):")
print("=" * 80)

query = """
SELECT * FROM daily_reports_brand_a 
WHERE branch = 'KRUS NA LIGAS'
  AND corporation = 'KRYPTON KNIGHT PAWNSHOP INC.'
  AND date = '2026-03-19' 
LIMIT 1
"""
result = db_manager.execute_query(query)

if result and cfg_result:
    row = result[0]
    credit_fields = cfg.get("Brand A", {}).get("credit", [])
    
    total = 0
    for field in credit_fields:
        label = field[0]
        db_col = field[2] if len(field) >= 3 else None
        if db_col and db_col in row:
            val = row[db_col]
            if val:
                try:
                    val_float = float(val)
                    total += val_float
                    print(f"{label:40s}: {val_float:12.2f}")
                except:
                    pass
    
    print("-" * 80)
    print(f"{'CALCULATED CREDIT TOTAL':40s}: {total:12.2f}")
    print(f"{'STORED CREDIT TOTAL':40s}: {row['credit_total']:12.2f}")
    
    if total != row['credit_total']:
        print(f"\n⚠️  DISCREPANCY: Stored value is {row['credit_total'] - total:+.2f} off")
        print(f"    Expected: {total:.2f}")
        print(f"    Actual:   {row['credit_total']:.2f}")
