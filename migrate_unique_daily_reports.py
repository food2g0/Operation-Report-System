"""
Migration: Add UNIQUE constraint to daily_reports tables.

PROBLEM
-------
Both `daily_reports` (Brand B) and `daily_reports_brand_a` (Brand A) lack a
UNIQUE KEY on (date, branch, corporation).  Without it:
  - Every client post creates a new row even for the same date/branch.
  - SUM queries (fund_transfer, report pages) multiply values by the number
    of duplicate rows.

FIX
---
1. Deduplicate each table — keep only the row with the highest `id` for every
   (date, branch, corporation) combination (latest submission wins).
2. Add UNIQUE KEY uq_daily_reports (date, branch, corporation) to
   `daily_reports`.
3. Add UNIQUE KEY uq_daily_reports_brand_a (date, branch, corporation) to
   `daily_reports_brand_a`.

Run once:  python migrate_unique_daily_reports.py
"""

import sys
from db_connect_pooled import db_manager


def count_duplicates(table: str) -> int:
    rows = db_manager.execute_query(
        f"""
        SELECT COUNT(*) AS cnt
        FROM {table} t
        INNER JOIN (
            SELECT date, branch, corporation, MAX(id) AS max_id
            FROM {table}
            GROUP BY date, branch, corporation
            HAVING COUNT(*) > 1
        ) dup ON t.date = dup.date
               AND t.branch = dup.branch
               AND t.corporation = dup.corporation
               AND t.id < dup.max_id
        """,
        ()
    )
    return rows[0]["cnt"] if rows else 0


def unique_key_exists(table: str, key_name: str) -> bool:
    rows = db_manager.execute_query(
        "SELECT COUNT(*) AS cnt FROM INFORMATION_SCHEMA.STATISTICS "
        "WHERE TABLE_SCHEMA = DATABASE() "
        "  AND TABLE_NAME = %s AND INDEX_NAME = %s",
        (table, key_name),
    )
    return bool(rows and rows[0]["cnt"] > 0)


def deduplicate(table: str) -> int:
    """Delete older duplicate rows, keep the one with the highest id."""
    result = db_manager.execute_query(
        f"""
        DELETE t1 FROM {table} t1
        INNER JOIN {table} t2
            ON  t1.date        = t2.date
            AND t1.branch      = t2.branch
            AND t1.corporation = t2.corporation
            AND t1.id          < t2.id
        """,
        ()
    )
    # execute_query may return the cursor rowcount as an int or a list
    if isinstance(result, int):
        return result
    return 0


def add_unique_key(table: str, key_name: str) -> None:
    db_manager.execute_query(
        f"ALTER TABLE `{table}` "
        f"ADD UNIQUE KEY `{key_name}` (`date`, `branch`, `corporation`)",
        ()
    )


def migrate_table(table: str, key_name: str) -> None:
    print(f"\n--- {table} ---")

    # Step 1: count duplicates
    dup_count = count_duplicates(table)
    print(f"  Duplicate rows to remove: {dup_count}")

    # Step 2: remove duplicates
    if dup_count > 0:
        deleted = deduplicate(table)
        print(f"  Deleted {deleted} duplicate row(s).")
    else:
        print("  No duplicates found — skipping DELETE.")

    # Step 3: add unique constraint
    if unique_key_exists(table, key_name):
        print(f"  SKIP  UNIQUE KEY `{key_name}` already exists.")
    else:
        print(f"  Adding UNIQUE KEY `{key_name}` (date, branch, corporation)...")
        try:
            add_unique_key(table, key_name)
            print(f"  OK    UNIQUE KEY `{key_name}` created.")
        except Exception as exc:
            print(f"  FAIL  Could not add unique key: {exc}")
            sys.exit(1)


def main() -> None:
    if not db_manager.test_connection():
        print("ERROR: Cannot connect to database.")
        sys.exit(1)

    print("=" * 60)
    print("Migration: Add UNIQUE constraints to daily_reports tables")
    print("=" * 60)

    migrate_table("daily_reports",        "uq_daily_reports")
    migrate_table("daily_reports_brand_a", "uq_daily_reports_brand_a")

    print("\nMigration complete.")
    print(
        "\nWhat changed:\n"
        "  * duplicate rows removed (latest id kept)\n"
        "  * re-posting the same date/branch now UPDATEs instead of INSERTing a new row\n"
        "  * fund_transfer cash_count / balance totals will no longer be multiplied\n"
    )


if __name__ == "__main__":
    main()
