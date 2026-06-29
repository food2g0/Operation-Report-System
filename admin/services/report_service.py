"""
Excel report generation service.

Target refactor: extracts logic from AdminDashboard._generate_full_brand_report
(admin/dashboard.py ~L3030 — currently ~2100 lines long).

This is the single largest refactoring target in the file.

Planned split:
  report_service.py         → orchestration, sheet list, date/filter resolution
  report_writers/
    dcc_sheet.py            → _write_dcc_sheet          (~350 lines)
    palawan_sheet.py        → _write_palawan_sheet       (~180 lines)
    ft_sheet.py             → _write_ft_sheet            (~400 lines)
    depo_br_sheet.py        → _write_depo_br_sheet       (~130 lines)
    pepp_sheet.py           → _write_pepp_report_sheet   (~270 lines)
    grouped_sheet.py        → _write_grouped_sheet        (~490 lines)

Coupling blockers:
  - _generate_full_brand_report receives `dialog` (QDialog) and updates
    a progress label on it
  - Sheet writers call back to self.db for SQL queries
  - Uses module-level _BRANCH_JOIN constant from dashboard.py
"""


def generate_full_brand_report(db, brand_label: str, account_type: int,
                               selected_date: str, filter_type: str,
                               filter_value: str, output_path: str) -> None:
    """
    Build a multi-sheet Excel workbook for the given brand and date.

    Args:
        db:           database manager (execute_query interface)
        brand_label:  "Brand A" or "Brand B"
        account_type: BRAND_A_TYPE (1) or BRAND_B_TYPE (2)
        selected_date: "YYYY-MM-DD"
        filter_type:  "corporation" | "os_group"
        filter_value: corporation name or group name
        output_path:  full filesystem path for the .xlsx file

    Raises:
        RuntimeError if openpyxl is not installed.
    """
    raise NotImplementedError(
        "Pending extraction from AdminDashboard._generate_full_brand_report"
    )
