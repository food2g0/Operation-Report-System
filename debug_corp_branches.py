#!/usr/bin/env python3
"""
Diagnostic script to check corporation and branch data.
Run this to debug why no branches appear in the report.
"""

from api_db_manager import db_manager

print("=" * 80)
print("DIAGNOSTIC: Corporation and Branch Data")
print("=" * 80)

# 1. List all corporations
print("\n1. CORPORATIONS IN DATABASE:")
print("-" * 80)
corps = db_manager.execute_query("SELECT id, name FROM corporations ORDER BY name")
if corps:
    for corp in corps:
        print(f"  ID: {corp['id']:3d} | Name: {corp['name']}")
else:
    print("  ERROR: No corporations found!")

# 2. List all branches with their corporation associations
print("\n2. BRANCHES WITH CORPORATION ASSOCIATIONS:")
print("-" * 80)
branches = db_manager.execute_query("""
    SELECT
        b.id,
        b.name,
        b.corporation_id,
        b.sub_corporation_id,
        COALESCE(sub_c.name, c.name) as corporation_name,
        b.os_name
    FROM branches b
    LEFT JOIN corporations c ON c.id = b.corporation_id
    LEFT JOIN corporations sub_c ON sub_c.id = b.sub_corporation_id
    ORDER BY b.name
    LIMIT 20
""")
if branches:
    for branch in branches:
        corp_id = branch['sub_corporation_id'] or branch['corporation_id']
        print(f"  Branch: {branch['name']:30} | Corp ID: {corp_id:3} | Corp Name: {branch['corporation_name']:30} | OS: {branch['os_name']}")
else:
    print("  ERROR: No branches found!")

# 3. Check for mismatches
print("\n3. CHECKING FOR DATA ISSUES:")
print("-" * 80)

# Check branches with no corporation_id
orphans = db_manager.execute_query("""
    SELECT COUNT(*) as count FROM branches
    WHERE corporation_id IS NULL AND sub_corporation_id IS NULL
""")
if orphans:
    print(f"  ⚠️  Branches with no corporation_id: {orphans[0]['count']}")

# Check if corporation names have whitespace issues
corps_with_space = db_manager.execute_query("""
    SELECT id, name,
           CHAR_LENGTH(name) - CHAR_LENGTH(TRIM(name)) as space_diff
    FROM corporations
    WHERE name != TRIM(name)
""")
if corps_with_space:
    print(f"  ⚠️  Corporations with leading/trailing spaces: {len(corps_with_space)}")
    for c in corps_with_space:
        print(f"      ID {c['id']}: '{c['name']}'")

print("\n" + "=" * 80)
print("If you see issues above, they may explain why no branches appear in reports.")
print("=" * 80)
