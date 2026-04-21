#!/usr/bin/env python3
from db_connect_pooled import db_manager

# Update the credit_total to the correct value
query = """
UPDATE daily_reports_brand_a 
SET credit_total = 32980.00
WHERE date = '2026-03-19'
  AND corporation = 'KRYPTON KNIGHT PAWNSHOP INC.'
  AND branch = 'KRUS NA LIGAS'
"""

print("=" * 80)
print("FIXING REPORT: KRYPTON KNIGHT PAWNSHOP INC. / KRUS NA LIGAS / 2026-03-19")
print("=" * 80)
print("Updating credit_total from 32982.00 → 32980.00")

result = db_manager.execute_query(query)
print(f"\nUpdate executed. Result: {result}")

# Verify the fix
verify_query = """
SELECT date, corporation, branch, credit_total 
FROM daily_reports_brand_a 
WHERE date = '2026-03-19'
  AND corporation = 'KRYPTON KNIGHT PAWNSHOP INC.'
  AND branch = 'KRUS NA LIGAS'
"""

verify = db_manager.execute_query(verify_query)
if verify:
    row = verify[0]
    print(f"\n✓ Verified: credit_total is now {row['credit_total']}")
else:
    print("Could not verify update")
