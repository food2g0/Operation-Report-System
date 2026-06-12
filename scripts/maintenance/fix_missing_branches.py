#!/usr/bin/env python3
"""
Identify and fix missing branch-corporation links.
"""

from api_db_manager import db_manager

print("=" * 80)
print("BRANCH-CORPORATION LINKING DIAGNOSTIC")
print("=" * 80)

# Get the corporation
corp_name = "ALLEXITE JEWELRY PAWNSHOP INC."
corp = db_manager.execute_query(
    "SELECT id FROM corporations WHERE name = %s",
    (corp_name,)
)

if not corp:
    print(f"ERROR: Corporation '{corp_name}' not found!")
    exit(1)

corp_id = corp[0]['id']
print(f"\n1. Corporation: {corp_name} (ID: {corp_id})")

# Get branches already linked
linked = db_manager.execute_query("""
    SELECT id, name FROM branches
    WHERE COALESCE(sub_corporation_id, corporation_id) = %s
    ORDER BY name
""", (corp_id,))

print(f"\n2. Currently linked branches ({len(linked)} total):")
linked_names = set()
for b in linked:
    print(f"   - {b['name']}")
    linked_names.add(b['name'].upper())

# Get ALL branches
all_branches = db_manager.execute_query(
    "SELECT id, name FROM branches ORDER BY name"
)

print(f"\n3. ALL branches in system ({len(all_branches)} total):")
for b in all_branches:
    linked_marker = "✓ LINKED" if b['name'].upper() in linked_names else "✗ NOT LINKED"
    print(f"   - {b['name']:40} {linked_marker}")

# Show unlinked branches
unlinked = [b for b in all_branches if b['name'].upper() not in linked_names]
print(f"\n4. UNLINKED branches ({len(unlinked)} total) that might belong to {corp_name}:")
for b in unlinked:
    print(f"   - {b['name']} (ID: {b['id']})")

print("\n" + "=" * 80)
print("WHAT TO DO:")
print("=" * 80)
print(f"""
If the {len(unlinked)} unlinked branches should belong to '{corp_name}':

1. Review the branch names above and identify which ones belong to {corp_name}
2. Run this command for each branch:

   UPDATE branches SET corporation_id = {corp_id}
   WHERE id = <branch_id>;

3. Or update multiple branches at once:

   UPDATE branches SET corporation_id = {corp_id}
   WHERE name IN ('Branch1', 'Branch2', ...);

4. Then generate the report again and all {len(linked) + len(unlinked)} branches should appear.

Note: Use sub_corporation_id instead of corporation_id if this is a sub-corporation.
""")
