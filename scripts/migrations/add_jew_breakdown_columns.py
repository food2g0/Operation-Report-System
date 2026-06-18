"""
Migration: add empeno_jew_new_breakdown and empeno_jew_renew_breakdown columns
to daily_reports and daily_reports_brand_a tables.

Run from the project root:
    python scripts/migrations/add_jew_breakdown_columns.py
"""
import sys
from pathlib import Path

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import mysql.connector
from secure_config import get_db_config

COLUMNS = [
    ("daily_reports",         "empeno_jew_new_breakdown"),
    ("daily_reports",         "empeno_jew_renew_breakdown"),
    ("daily_reports_brand_a", "empeno_jew_new_breakdown"),
    ("daily_reports_brand_a", "empeno_jew_renew_breakdown"),
]


def run():
    cfg = get_db_config()
    if not cfg:
        print("ERROR: Could not load DB config (db_config.enc missing or corrupt).")
        sys.exit(1)

    print(f"Connecting to {cfg['host']}:{cfg.get('port', 3306)} / {cfg['database']} ...")
    conn = mysql.connector.connect(
        host=cfg["host"],
        port=int(cfg.get("port", 3306)),
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        connection_timeout=10,
    )
    cursor = conn.cursor()

    for table, col in COLUMNS:
        # Check if column already exists
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """, (cfg["database"], table, col))
        (exists,) = cursor.fetchone()

        if exists:
            print(f"  SKIP  {table}.{col}  (already exists)")
        else:
            sql = f"ALTER TABLE `{table}` ADD COLUMN `{col}` TEXT DEFAULT NULL"
            cursor.execute(sql)
            conn.commit()
            print(f"  ADDED {table}.{col}")

    cursor.close()
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    run()
