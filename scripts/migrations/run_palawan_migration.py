"""
Manual Palawan migration: copies palawan details from daily_reports and
daily_reports_brand_a into payable_tbl_brand_a, then zeroes out the
source columns.  Skips rows that already exist in payable_tbl_brand_a.

Run from the project root:
    python scripts/migrations/run_palawan_migration.py
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import mysql.connector
from secure_config import get_db_config

# ── helpers ───────────────────────────────────────────────────────────────────

def _conn():
    cfg = get_db_config()
    if not cfg:
        print("ERROR: Could not load DB config.")
        sys.exit(1)
    return mysql.connector.connect(
        host=cfg["host"],
        port=int(cfg.get("port", 3306)),
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        connection_timeout=10,
    )

SELECT_PALAWAN = """
    SELECT
        corporation, branch, date,
        palawan_sendout_lotes_total      AS so_lotes,
        palawan_sendout_principal        AS so_principal,
        palawan_sendout_sc               AS so_sc,
        palawan_sendout_commission       AS so_commission,
        palawan_sendout_regular_total    AS so_total,
        palawan_payout_lotes_total       AS po_lotes,
        palawan_payout_principal         AS po_principal,
        palawan_payout_sc                AS po_sc,
        palawan_payout_commission        AS po_commission,
        palawan_payout_regular_total     AS po_total,
        palawan_international_lotes_total    AS int_lotes,
        palawan_international_principal      AS int_principal,
        palawan_international_sc             AS int_sc,
        palawan_international_commission     AS int_commission,
        palawan_international_regular_total  AS int_total,
        palawan_pay_out_incentives       AS inc,
        palawan_suki_discounts           AS skid,
        palawan_suki_rebates             AS skir,
        palawan_cancel                   AS cancellation
    FROM {table}
    WHERE (palawan_sendout_principal      > 0
        OR palawan_payout_principal       > 0
        OR palawan_international_principal > 0
        OR palawan_pay_out_incentives     > 0
        OR palawan_suki_discounts         > 0
        OR palawan_suki_rebates           > 0
        OR palawan_cancel                 > 0)
    ORDER BY date DESC, corporation, branch
"""

INSERT_PAYABLE = """
    INSERT INTO payable_tbl_brand_a
        (corporation, branch, date,
         sendout_lotes, sendout_capital, sendout_sc, sendout_commission, sendout_total,
         payout_lotes,  payout_capital,  payout_sc,  payout_commission,  payout_total,
         international_lotes, international_capital, international_sc,
         international_commission, international_total,
         inc, skid, skir, cancellation)
    VALUES (%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s)
"""

ZERO_PALAWAN = """
    UPDATE {table}
    SET palawan_sendout_principal          = 0,
        palawan_sendout_sc                 = 0,
        palawan_sendout_commission         = 0,
        palawan_sendout_regular_total      = 0,
        palawan_sendout_lotes_total        = 0,
        palawan_payout_principal           = 0,
        palawan_payout_sc                  = 0,
        palawan_payout_commission          = 0,
        palawan_payout_regular_total       = 0,
        palawan_payout_lotes_total         = 0,
        palawan_international_principal    = 0,
        palawan_international_sc           = 0,
        palawan_international_commission   = 0,
        palawan_international_regular_total= 0,
        palawan_international_lotes_total  = 0,
        palawan_pay_out_incentives         = 0,
        palawan_suki_discounts             = 0,
        palawan_suki_rebates               = 0,
        palawan_cancel                     = 0
    WHERE corporation=%s AND branch=%s AND date=%s
"""

# ── main ──────────────────────────────────────────────────────────────────────

def migrate_table(cursor, table_name):
    print(f"\n{'='*60}")
    print(f"  Source: {table_name}")
    print(f"{'='*60}")

    cursor.execute(SELECT_PALAWAN.format(table=table_name))
    rows = cursor.fetchall()

    if not rows:
        print("  No palawan data found — nothing to migrate.")
        return 0, 0

    print(f"  Found {len(rows)} row(s) with palawan data.")

    migrated = skipped = 0
    for r in rows:
        corp, branch, date = r["corporation"], r["branch"], r["date"]

        # Check duplicate
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM payable_tbl_brand_a "
            "WHERE corporation=%s AND branch=%s AND date=%s",
            (corp, branch, date),
        )
        if cursor.fetchone()["cnt"] > 0:
            print(f"  SKIP  (already exists) {branch} {date} [{corp}]")
            skipped += 1
            continue

        try:
            cursor.execute(INSERT_PAYABLE, (
                corp, branch, date,
                r["so_lotes"],  r["so_principal"],  r["so_sc"],
                r["so_commission"],  r["so_total"],
                r["po_lotes"],  r["po_principal"],  r["po_sc"],
                r["po_commission"],  r["po_total"],
                r["int_lotes"], r["int_principal"], r["int_sc"],
                r["int_commission"], r["int_total"],
                r["inc"], r["skid"], r["skir"], r["cancellation"],
            ))
            cursor.execute(ZERO_PALAWAN.format(table=table_name), (corp, branch, date))
            print(f"  OK    {branch} {date} [{corp}]")
            migrated += 1
        except Exception as exc:
            print(f"  ERROR {branch} {date} [{corp}]: {exc}")

    print(f"\n  Result: {migrated} migrated, {skipped} skipped (duplicates)")
    return migrated, skipped


def main():
    print(f"\nPalawan Migration  —  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    cfg = get_db_config()
    print(f"Connecting to {cfg['host']}:{cfg.get('port', 3306)} / {cfg['database']} ...")

    conn = _conn()
    conn.autocommit = False
    cursor = conn.cursor(dictionary=True)

    try:
        m1, s1 = migrate_table(cursor, "daily_reports")           # Brand B
        m2, s2 = migrate_table(cursor, "daily_reports_brand_a")   # Brand A

        conn.commit()

        print(f"\n{'='*60}")
        print(f"  TOTAL: {m1+m2} migrated, {s1+s2} skipped")
        print(f"{'='*60}\n")

    except Exception as exc:
        conn.rollback()
        print(f"\nCRITICAL ERROR — rolled back all changes: {exc}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
