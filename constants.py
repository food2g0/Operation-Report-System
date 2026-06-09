"""
Global constants and configuration for the Operation Report System.
Centralized for easier maintenance and consistency.
"""

# ── Colors ────────────────────────────────────────────────────────────────
COLORS = {
    # Brand Primary Colors
    "primary": "#27AE60",
    "primary_dark": "#1E8449",
    "primary_darker": "#219A52",
    "primary_light": "#D5F4E6",
    "primary_bg": "#f5f6fa",

    # Status Colors
    "success": "#27AE60",
    "warning": "#F39C12",
    "warning_bg": "#fff3cd",
    "warning_border": "#ffeaa7",
    "warning_text": "#856404",
    "danger": "#E74C3C",
    "info": "#3498DB",
    "info_dark": "#2980B9",
    "info_darker": "#21618C",

    # UI Button Colors
    "btn_primary": "#27AE60",
    "btn_primary_hover": "#219A52",
    "btn_warning": "#F39C12",
    "btn_warning_hover": "#E67E22",

    # Grays
    "text_dark": "#2C3E50",
    "text_secondary": "#34495E",
    "text_light": "#495057",
    "light_gray": "#ECF0F1",
    "lighter_gray": "#F8F9FA",
    "medium_gray": "#95A5A6",
    "dark_gray": "#34495E",
    "border": "#BDC3C7",
    "border_light": "#DEE2E6",

    # Specific UI Colors
    "debit": "#27AE60",      # Green
    "credit": "#E74C3C",     # Red
    "summary": "#F39C12",    # Orange
    "total": "#E2EFDA",      # Light green
    "header": "#2C3E50",     # Dark blue-gray

    # Excel Report Colors (without #)
    "debit_fill": "27AE60",
    "credit_fill": "E74C3C",
    "summary_fill": "F39C12",
    "total_fill": "E2EFDA",
    "header_fill": "2C3E50",
    "info_fill": "D5F4E6",
}

# ── Fonts ─────────────────────────────────────────────────────────────────
FONT_SIZES = {
    "title": 14,
    "header": 12,
    "normal": 11,
    "small": 10,
}

# ── Style Sheets ──────────────────────────────────────────────────────────
BUTTON_STYLE = """
    QPushButton {{
        background-color: {bg_color};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 11px;
    }}
    QPushButton:hover {{
        background-color: {hover_color};
    }}
    QPushButton:pressed {{
        background-color: {press_color};
    }}
"""

PRIMARY_BUTTON_STYLE = BUTTON_STYLE.format(
    bg_color=COLORS["primary"],
    hover_color=COLORS["primary_dark"],
    press_color="#186A3B",
)

DANGER_BUTTON_STYLE = BUTTON_STYLE.format(
    bg_color=COLORS["danger"],
    hover_color="#C0392B",
    press_color="#A93226",
)

INPUT_STYLE = """
    QLineEdit, QSpinBox, QDoubleSpinBox {{
        padding: 6px;
        border: 1px solid {border};
        border-radius: 3px;
        font-size: 11px;
        background-color: white;
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {primary};
        outline: none;
    }}
    QLineEdit:read-only, QSpinBox:read-only, QDoubleSpinBox:read-only {{
        background-color: {light_gray};
        color: {medium_gray};
    }}
""".format(
    border=COLORS["border"],
    primary=COLORS["primary"],
    light_gray=COLORS["light_gray"],
    medium_gray=COLORS["medium_gray"],
)

# ── Configuration ─────────────────────────────────────────────────────────
CONFIG = {
    "session_timeout_minutes": 30,
    "cache_ttl_seconds": 30,
    "schema_cache_ttl": 3600,  # 1 hour
    "list_cache_ttl": 300,     # 5 minutes
    "default_zoom_level": 100,
    "max_zoom": 150,
    "min_zoom": 80,
    "zoom_step": 10,
}

# ── Table Names ───────────────────────────────────────────────────────────
TABLES = {
    "daily_cash_count": "daily_report",
    "palawan": "palawan_details",
    "money_changer": "money_changer",
    "branches": "branches",
    "corporations": "corporations",
    "users": "users",
}

# ── Status Messages ───────────────────────────────────────────────────────
MESSAGES = {
    "no_data": "No data found for the selected criteria.",
    "save_success": "Data saved successfully.",
    "save_error": "Error saving data. Please try again.",
    "delete_success": "Data deleted successfully.",
    "delete_error": "Error deleting data. Please try again.",
    "export_success": "Report exported successfully to:\n{}",
    "export_error": "Error exporting report: {}",
    "offline_warning": "⚠ No internet connection — you can continue inputting data and save drafts, but cannot post.",
}
