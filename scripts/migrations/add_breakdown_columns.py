"""
Migration: add all breakdown columns to daily_reports and daily_reports_brand_a.

Columns added (idempotent — skips any that already exist):
  ft_ho_breakdown           TEXT  — Fund Transfer to HO bank breakdown (JSON)
  pc_salary_breakdown       TEXT  — PC-Salary per-person breakdown (JSON, Brand A only)
  empeno_motor_car_breakdown TEXT  — Empeno Motor/Car breakdown (JSON)
  empeno_jew_new_breakdown  TEXT  — Empeno JEW New breakdown (JSON)
  empeno_jew_renew_breakdown TEXT  — Empeno JEW Renew breakdown (JSON)

Run from the project root:
    python scripts/migrations/add_breakdown_columns.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import mysql.connector
from secure_config import get_db_config

TABLES = ["daily_reports", "daily_reports_brand_a"]

COLUMNS = [
    "ft_ho_breakdown",
    "pc_salary_breakdown",
    "empeno_motor_car_breakdown",
    "empeno_jew_new_breakdown",
    "empeno_jew_renew_breakdown",
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

    for table in TABLES:
        print(f"\nTable: {table}")
        for col in COLUMNS:
            cursor.execute(
                """
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
                """,
                (cfg["database"], table, col),
            )
            (exists,) = cursor.fetchone()

            if exists:
                print(f"  SKIP   {col}  (already exists)")
            else:
                cursor.execute(
                    f"ALTER TABLE `{table}` ADD COLUMN `{col}` TEXT DEFAULT NULL"
                )
                conn.commit()
                print(f"  ADDED  {col}")

    cursor.close()
    conn.close()
    print("\nDone. Run the app — breakdowns should now save and display correctly.")


if __name__ == "__main__":
    run()
