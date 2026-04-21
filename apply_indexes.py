"""
Apply performance indexes directly from Python — no server SSH needed.
Run: python apply_indexes.py
"""
from db_connect_pooled import db_manager

INDEXES = [
    # (table, index_name, columns)
    # daily_reports (Brand B)
    ("daily_reports", "idx_dr_corp_date", "corporation, date"),
    ("daily_reports", "idx_dr_branch_date", "branch, date"),
    ("daily_reports", "idx_dr_date", "date"),
    ("daily_reports", "idx_dr_corp_branch_date", "corporation, branch, date"),
    ("daily_reports", "idx_dr_variance", "variance_status, corporation, date"),
    # daily_reports_brand_a (Brand A)
    ("daily_reports_brand_a", "idx_dra_corp_date", "corporation, date"),
    ("daily_reports_brand_a", "idx_dra_branch_date", "branch, date"),
    ("daily_reports_brand_a", "idx_dra_date", "date"),
    ("daily_reports_brand_a", "idx_dra_corp_branch_date", "corporation, branch, date"),
    ("daily_reports_brand_a", "idx_dra_variance", "variance_status, corporation, date"),
    # branches
    ("branches", "idx_branches_name", "name"),
    ("branches", "idx_branches_os", "os_name"),
    ("branches", "idx_branches_global", "global_tag"),
    ("branches", "idx_branches_os_registered", "os_name, is_registered"),
    ("branches", "idx_branches_global_os", "global_tag, os_name, is_registered"),
    # payable tables
    ("payable_tbl", "idx_pay_corp_date", "corporation, date"),
    ("payable_tbl", "idx_pay_corp_branch_date", "corporation, branch, date"),
    ("payable_tbl_brand_a", "idx_paya_corp_date", "corporation, date"),
    ("payable_tbl_brand_a", "idx_paya_corp_branch_date", "corporation, branch, date"),
    # other service tables
    ("daily_transaction_tbl_brand_a", "idx_dt_corp_date", "corporation, date"),
    ("other_services_tbl_brand_a", "idx_os_corp_date", "corporation, date"),
    ("global_other_services_tbl", "idx_gos_branch_date", "branch, date"),
    ("global_other_services_tbl", "idx_gos_date", "date"),
    # cash_float_tbl
    ("cash_float_tbl", "idx_cf_branch_corp_date", "branch, corporation, date"),
    # extra_space_fund_transfer
    ("extra_space_fund_transfer", "idx_esft_date", "report_date"),
]


def index_exists(table, index_name):
    result = db_manager.execute_query(
        "SELECT COUNT(*) AS cnt FROM INFORMATION_SCHEMA.STATISTICS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND INDEX_NAME = %s",
        (table, index_name),
    )
    return result and result[0]["cnt"] > 0


def apply_indexes():
    if not db_manager.test_connection():
        print("Cannot connect to database.")
        return

    created, skipped, failed = 0, 0, 0

    for table, idx_name, columns in INDEXES:
        if index_exists(table, idx_name):
            print(f"  SKIP  {table}.{idx_name} (already exists)")
            skipped += 1
            continue

        sql = f"ALTER TABLE `{table}` ADD INDEX `{idx_name}` ({columns})"
        try:
            db_manager.execute_query(sql)
            print(f"  OK    {table}.{idx_name}")
            created += 1
        except Exception as e:
            print(f"  FAIL  {table}.{idx_name} — {e}")
            failed += 1

    print(f"\nDone: {created} created, {skipped} already existed, {failed} failed")


# Tables whose string columns must share the same collation for JOINs to work
COLLATION_TABLES = [
    "daily_reports",
    "daily_reports_brand_a",
    "branches",
    "corporations",
    "cash_float_tbl",
    "payable_tbl",
    "payable_tbl_brand_a",
    "global_other_services_tbl",
    "other_services_tbl_brand_a",
    "daily_transaction_tbl_brand_a",
    "extra_space_fund_transfer",
]

TARGET_COLLATION = "utf8mb4_general_ci"
TARGET_CHARSET = "utf8mb4"


def fix_collations():
    """Convert all key tables to utf8mb4_general_ci to prevent collation mismatch errors."""
    if not db_manager.test_connection():
        print("Cannot connect to database.")
        return

    fixed, skipped, failed = 0, 0, 0

    for table in COLLATION_TABLES:
        # Check current collation
        row = db_manager.execute_query(
            "SELECT TABLE_COLLATION FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
            (table,)
        )
        if not row:
            print(f"  SKIP  {table} (table not found)")
            skipped += 1
            continue

        current = row[0].get("TABLE_COLLATION", "")
        if current == TARGET_COLLATION:
            print(f"  SKIP  {table} (already {TARGET_COLLATION})")
            skipped += 1
            continue

        sql = (
            f"ALTER TABLE `{table}` CONVERT TO "
            f"CHARACTER SET {TARGET_CHARSET} COLLATE {TARGET_COLLATION}"
        )
        try:
            db_manager.execute_query(sql)
            print(f"  OK    {table} ({current} -> {TARGET_COLLATION})")
            fixed += 1
        except Exception as e:
            print(f"  FAIL  {table} — {e}")
            failed += 1

    print(f"\nDone: {fixed} converted, {skipped} already correct, {failed} failed")


if __name__ == "__main__":
    print("Applying performance indexes...\n")
    apply_indexes()
    print("\n\nFixing table collations...\n")
    fix_collations()
