"""
Entry reset service.

Target refactor: extracts DB logic from AdminDashboard.reset_entry
(admin/dashboard.py ~L2574).

Business rules that MUST be preserved:
  - Unlock: UPDATE daily_reports_brand_a SET is_locked = 0
  - Unlock: UPDATE daily_reports SET is_locked = 0
  - Delete: DELETE FROM cash_float_tbl  (stale supplement)
  - NEVER DELETE OR MODIFY payable_tbl_brand_a (intentionally preserved)

Coupling blockers:
  - reset_entry shows QMessageBox.question (confirm) and .information (result)
  - Calls self._notify_entry_reset() which fires an HTTP API call
"""

MAIN_TABLES = ["daily_reports_brand_a", "daily_reports"]
SUPP_TABLES = ["cash_float_tbl"]
# payable_tbl_brand_a is intentionally excluded — do NOT add it here


def unlock_entry(db, branch: str, date: str) -> bool:
    """
    Set is_locked = 0 for `branch` / `date` in both brand tables.

    Returns True if at least one table had a matching row.

    Raises:
        Nothing — callers are expected to catch and display errors.
    """
    found = False

    for table in MAIN_TABLES:
        # Ensure the is_locked column exists (backward compat)
        col_check = db.execute_query(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s "
            "AND COLUMN_NAME = 'is_locked'",
            [table]
        )
        if not col_check:
            db.execute_query(
                f"ALTER TABLE {table} "
                "ADD COLUMN is_locked TINYINT(1) NOT NULL DEFAULT 1"
            )

        check = db.execute_query(
            f"SELECT COUNT(*) AS cnt FROM {table} "
            "WHERE branch = %s AND date = %s",
            [branch, date]
        )
        if check and check[0].get('cnt', 0) > 0:
            found = True
            db.execute_query(
                f"UPDATE {table} SET is_locked = 0 "
                "WHERE branch = %s AND date = %s",
                [branch, date]
            )

    return found


def clear_supplement_tables(db, branch: str, date: str) -> None:
    """
    Delete stale supplementary data so resubmissions start fresh.
    Only deletes from SUPP_TABLES — payable_tbl_brand_a is never touched.
    """
    for table in SUPP_TABLES:
        try:
            db.execute_query(
                f"DELETE FROM {table} WHERE branch = %s AND date = %s",
                [branch, date]
            )
        except Exception:
            pass  # missing table is non-fatal
