"""
fix_totals_db.py — Recalculate and update debit_total, credit_total,
ending_balance, and cash_result for ALL existing records in both
daily_reports and daily_reports_brand_a tables.

Formula:
  debit_total    = beginning_balance + SUM(all debit fields)
  credit_total   = SUM(all credit fields)
  ending_balance = debit_total - credit_total
  cash_result    = cash_count - ending_balance

Run once from the project root:
    python fix_totals_db.py
"""

import sys
from db_connect_pooled import db_manager

# ── Field definitions per table ───────────────────────────────────────────────
# These match the hardcoded fallback in admin_dashboard.py.
# If your field_config is customised per brand, update these lists accordingly.

DEBIT_FIELDS_BRAND_B = [
    "rescate_jewelry", "interest", "penalty", "stamp", "resguardo_affidavit",
    "habol_renew_tubos", "habol_rt_interest_stamp", "jew_ai", "sc",
    "fund_transfer_from_branch", "sendah_load_sc", "ppay_co_sc",
    "palawan_send_out", "palawan_sc", "palawan_suki_card",
    "palawan_pay_cash_in_sc", "palawan_pay_bills_sc", "palawan_load",
    "palawan_change_receiver", "mc_in", "handling_fee", "other_penalty",
    "cash_overage",
]

CREDIT_FIELDS_BRAND_B = [
    "empeno_jew_new", "empeno_jew_renew", "empeno_motor_car",
    "fund_transfer_to_head_office", "fund_transfer_to_branch",
    "palawan_pay_out", "palawan_pay_out_incentives", "palawan_pay_cash_out",
    "mc_out", "pc_salary", "pc_rental", "pc_electric", "pc_water",
    "pc_internet", "pc_lbc_jrs_jnt", "pc_permits_bir_payments",
    "pc_supplies_xerox_maintenance", "pc_transpo", "palawan_cancel",
    "palawan_suki_discounts", "palawan_suki_rebates", "others", "cash_shortage",
]

# Brand A uses the same structure (adjust if Brand A has different fields)
DEBIT_FIELDS_BRAND_A  = DEBIT_FIELDS_BRAND_B
CREDIT_FIELDS_BRAND_A = CREDIT_FIELDS_BRAND_B

TABLE_CONFIG = [
    ("daily_reports",         DEBIT_FIELDS_BRAND_B, CREDIT_FIELDS_BRAND_B),
    ("daily_reports_brand_a", DEBIT_FIELDS_BRAND_A, CREDIT_FIELDS_BRAND_A),
]


def get_existing_cols(table):
    rows = db_manager.execute_query(
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
        (table,)
    )
    return {r["COLUMN_NAME"] for r in rows} if rows else set()


def fix_table(table, debit_fields, credit_fields):
    print(f"\n{'='*60}")
    print(f"Table: {table}")

    existing = get_existing_cols(table)
    if not existing:
        print("  Table not found or no columns — skipping.")
        return

    d_cols = [c for c in debit_fields if c in existing]
    c_cols = [c for c in credit_fields if c in existing]

    # Fetch all records (only the columns we need)
    select_cols = (
        ["id", "beginning_balance", "cash_count"]
        + d_cols + c_cols
    )
    sel = ", ".join(f"`{c}`" for c in select_cols)
    rows = db_manager.execute_query(f"SELECT {sel} FROM `{table}`") or []

    print(f"  Records to process: {len(rows)}")

    updated = 0
    skipped = 0
    BATCH = 10   # commit/send in small batches to avoid rate-limit

    for i, row in enumerate(rows):
        rec_id   = row["id"]
        beginning = float(row.get("beginning_balance") or 0)
        cash_count = float(row.get("cash_count") or 0)

        debit_sum  = sum(float(row.get(c) or 0) for c in d_cols)
        credit_sum = sum(float(row.get(c) or 0) for c in c_cols)

        debit_total    = beginning + debit_sum
        credit_total   = credit_sum
        ending_balance = debit_total - credit_total
        cash_result    = cash_count - ending_balance

        try:
            affected = db_manager.execute_query(
                f"""UPDATE `{table}`
                    SET debit_total    = %s,
                        credit_total   = %s,
                        ending_balance = %s,
                        cash_result    = %s
                    WHERE id = %s""",
                (debit_total, credit_total, ending_balance, cash_result, rec_id)
            )
            updated += 1
        except Exception as e:
            print(f"  ERROR updating id={rec_id}: {e}")
            skipped += 1

        # Small pause every BATCH rows to stay under Nginx rate limit
        if (i + 1) % BATCH == 0:
            import time; time.sleep(0.6)

    print(f"  Updated : {updated}")
    if skipped:
        print(f"  Skipped : {skipped}")
    print(f"  Done.")


def main():
    print("ORS — Recalculate totals in daily_reports tables")
    print("This will overwrite debit_total, credit_total, ending_balance, cash_result")
    confirm = input("Proceed? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        sys.exit(0)

    for table, d_fields, c_fields in TABLE_CONFIG:
        fix_table(table, d_fields, c_fields)

    print("\nAll done. Run the application and verify a few entries.")


if __name__ == "__main__":
    main()
