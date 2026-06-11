#!/usr/bin/env python3
"""
Test script to verify corporation filter works correctly.
Run this to test if the report query would return branches.
"""

from api_db_manager import db_manager
from datetime import datetime, timedelta

print("=" * 80)
print("TEST: Corporation Report Filter")
print("=" * 80)

# Get a corporation to test with
corps = db_manager.execute_query("SELECT id, name FROM corporations LIMIT 1")
if not corps:
    print("ERROR: No corporations in database!")
    exit(1)

corp_name = corps[0]['name'].strip()
print(f"\n1. Testing with corporation: '{corp_name}'")

# Test date - use today
test_date = datetime.now().strftime("%Y-%m-%d")
print(f"2. Testing with date: {test_date}")

# Test 1: Simple branch count for this corporation (no date filter)
print("\n3. Simple branch count test:")
count_result = db_manager.execute_query("""
    SELECT COUNT(*) as count
    FROM branches b
    INNER JOIN corporations c ON c.id = COALESCE(b.sub_corporation_id, b.corporation_id)
    WHERE c.name COLLATE utf8mb4_general_ci = %s
""", (corp_name,))
if count_result:
    print(f"   Branches for '{corp_name}': {count_result[0]['count']}")

# Test 2: The actual query structure from the report
print("\n4. Report query test (daily_reports_brand_a):")
branches = db_manager.execute_query("""
    SELECT b.name AS branch
    FROM branches b
    INNER JOIN corporations c ON c.id = COALESCE(b.sub_corporation_id, b.corporation_id)
    LEFT JOIN daily_reports_brand_a dr
      ON b.name COLLATE utf8mb4_general_ci = dr.branch COLLATE utf8mb4_general_ci
      AND dr.date = %s
    WHERE c.name COLLATE utf8mb4_general_ci = %s
    GROUP BY b.name
    ORDER BY b.name
    LIMIT 10
""", (test_date, corp_name))

if branches:
    print(f"   Found {len(branches)} branches:")
    for b in branches:
        print(f"     - {b['branch']}")
else:
    print(f"   ⚠️  NO BRANCHES FOUND!")
    print(f"\n   Debugging why...")

    # Check if corporation exists
    corp_check = db_manager.execute_query(
        "SELECT id FROM corporations WHERE name COLLATE utf8mb4_general_ci = %s",
        (corp_name,)
    )
    if corp_check:
        corp_id = corp_check[0]['id']
        print(f"   ✓ Corporation exists with ID: {corp_id}")

        # Check branches for this corp
        branch_check = db_manager.execute_query(
            "SELECT COUNT(*) as count FROM branches WHERE COALESCE(sub_corporation_id, corporation_id) = %s",
            (corp_id,)
        )
        if branch_check:
            print(f"   ✓ Branches linked to this corp: {branch_check[0]['count']}")
    else:
        print(f"   ✗ Corporation '{corp_name}' not found!")

# Test 3: With registration filter
print("\n5. Report query with registration filter (registered only):")
branches_reg = db_manager.execute_query("""
    SELECT b.name AS branch
    FROM branches b
    INNER JOIN corporations c ON c.id = COALESCE(b.sub_corporation_id, b.corporation_id)
    LEFT JOIN daily_reports_brand_a dr
      ON b.name COLLATE utf8mb4_general_ci = dr.branch COLLATE utf8mb4_general_ci
      AND dr.date = %s
    WHERE c.name COLLATE utf8mb4_general_ci = %s
      AND b.is_registered = 1
    GROUP BY b.name
    ORDER BY b.name
    LIMIT 10
""", (test_date, corp_name))

if branches_reg:
    print(f"   Found {len(branches_reg)} registered branches")
else:
    print(f"   No registered branches found (or none marked as registered)")

print("\n" + "=" * 80)
