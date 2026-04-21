"""
Super Admin Dashboard
=====================
Provides field management for Brand A and Brand B cash-flow debit/credit
sections, as well as access to User Management.

Field changes are persisted to  field_config.json  in the same directory
and are picked up by the Client dashboard on the next load / brand switch.
"""

import json
import os
import re

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QMessageBox, QScrollArea, QFrame, QLineEdit,
    QComboBox, QSizePolicy, QStackedWidget, QFormLayout, QSplitter,
    QCheckBox, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from db_connect_pooled import db_manager
from security import SessionManager
from ping_monitor import PingMonitorWindow

# Optional auto-updater
try:
    from auto_updater import check_for_updates, check_update_success
    from version import __version__
    AUTO_UPDATE_ENABLED = True
except ImportError:
    AUTO_UPDATE_ENABLED = False
    __version__ = "1.0.0"
    check_update_success = None

# ── path to the shared field config ──────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIELD_CONFIG_PATH = os.path.join(_BASE_DIR, "field_config.json")

# ── default fields (used when config file is absent) ─────────────────────────
_BRAND_A_DEBIT_DEFAULTS = [
    ["Rescate Jewelry", "Enter Rescate Jewelry", "rescate_jewelry"],
    ["Interest", "Enter Interest", "interest"],
    ["Penalty", "Enter Penalty", "penalty"],
    ["Cash Overage", "Enter Cash Overage", "cash_overage"],
]
_BRAND_A_CREDIT_DEFAULTS = [
    ["Empeno JEW. (NEW)", "Enter Empeno Jew", "empeno_jew_new"],
    ["Cash Shortage", "Enter Cash Shortage", "cash_shortage"],
]
_BRAND_B_DEBIT_DEFAULTS = [
    ["Rescate Jewelry", "Enter Rescate Jewelry", "rescate_jewelry"],
    ["Interest", "Enter Interest", "interest"],
    ["Penalty", "Enter Penalty", "penalty"],
    ["Cash Overage", "Enter Cash Overage", "cash_overage"],
]
_BRAND_B_CREDIT_DEFAULTS = [
    ["Empeno JEW. (NEW)", "Enter Empeno Jew", "empeno_jew_new"],
    ["Cash Shortage", "Enter Cash Shortage", "cash_shortage"],
]


# ─────────────────────────────────────────────────────────────────────────────
def _load_field_config_from_db() -> dict:
    """Load field config from database. Returns None if not found or error."""
    try:
        result = db_manager.execute_query(
            "SELECT config_value FROM field_config WHERE config_key = 'field_definitions'"
        )
        if result and result[0].get('config_value'):
            return json.loads(result[0]['config_value'])
    except Exception as exc:
        print(f"[SuperAdmin] Failed to load config from DB: {exc}")
    return None


def _save_field_config_to_db(cfg: dict, username: str = None) -> bool:
    """Save field config to database. Returns True on success."""
    try:
        config_json = json.dumps(cfg, ensure_ascii=False)
        sql = """
            INSERT INTO field_config (config_key, config_value, updated_by)
            VALUES ('field_definitions', %s, %s)
            ON DUPLICATE KEY UPDATE config_value = VALUES(config_value), updated_by = VALUES(updated_by)
        """
        result = db_manager.execute_query(sql, (config_json, username or 'super_admin'))
        return result is not None
    except Exception as exc:
        print(f"[SuperAdmin] Failed to save config to DB: {exc}")
        return False


def load_field_config() -> dict:
    """Load field config from database first, fall back to file."""
    # Try database first (central storage for all clients)
    db_cfg = _load_field_config_from_db()
    if db_cfg:
        # Ensure expected structure
        for brand in ("Brand A", "Brand B"):
            db_cfg.setdefault(brand, {})
            db_cfg[brand].setdefault("credit", [])
            db_cfg[brand].setdefault("debit", [])
        return db_cfg
    
    # Fall back to file
    try:
        with open(FIELD_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # Ensure expected structure
        for brand in ("Brand A", "Brand B"):
            cfg.setdefault(brand, {})
            cfg[brand].setdefault("credit", [])
            cfg[brand].setdefault("debit", [])
        return cfg
    except FileNotFoundError:
        return {
            "Brand A": {"debit": _BRAND_A_DEBIT_DEFAULTS[:], "credit": _BRAND_A_CREDIT_DEFAULTS[:]},
            "Brand B": {"debit": _BRAND_B_DEBIT_DEFAULTS[:], "credit": _BRAND_B_CREDIT_DEFAULTS[:]},
        }
    except Exception as exc:
        print(f"[SuperAdmin] Failed to load field config: {exc}")
        return {
            "Brand A": {"debit": [], "credit": []},
            "Brand B": {"debit": [], "credit": []},
        }


def save_field_config(cfg: dict) -> bool:
    """Persist the config to both database and disk. Returns True on success."""
    success = True
    
    # Save to database first (primary storage for clients)
    if not _save_field_config_to_db(cfg):
        print("[SuperAdmin] Warning: Failed to save config to database")
        success = False
    
    # Also save to local file (backup)
    try:
        with open(FIELD_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        print(f"[SuperAdmin] Failed to save field config to file: {exc}")
        # Database save is more important, only fail if both failed
        if not success:
            return False
    
    return True


def _ensure_db_columns(db_col: str, report_tables: list = None) -> tuple:
    """
    Make sure the required tables have the two columns for a new field::

        <db_col>        DECIMAL(15,2) DEFAULT 0   (amount)
        <db_col>_lotes  SMALLINT DEFAULT 0        (transaction count)

    Args:
        db_col: The database column name
        report_tables: List of additional report tables to add columns to.
                       Options: 'daily_transaction', 'pnl', 'other_services'

    Returns (success: bool, message: str).
    Skips silently if the column already exists (MySQL's IF NOT EXISTS).
    """
    # Base tables always included
    tables = ["daily_reports", "daily_reports_brand_a"]
    
    # Report table mapping
    report_table_map = {
        'daily_transaction': 'daily_transaction_tbl_brand_a',
        'pnl': 'PL_tbl_brand_a',
        'other_services': 'other_services_tbl_brand_a'
    }
    
    # Add selected report tables
    if report_tables:
        for rt in report_tables:
            if rt in report_table_map:
                tables.append(report_table_map[rt])
    
    errors = []
    updated_tables = []

    # Verify db_manager is available
    if not db_manager.test_connection():
        return False, "Cannot connect to the database."

    for table in tables:
        # Check if the table exists first
        try:
            exists = db_manager.execute_query(
                "SELECT COUNT(*) AS cnt FROM information_schema.tables "
                "WHERE table_schema = DATABASE() AND table_name = %s",
                [table]
            )
            if not exists or exists[0]['cnt'] == 0:
                continue  # Table doesn't exist – skip without error
        except Exception:
            continue

        table_updated = False
        for col_name, col_type in [
            (db_col,           "DECIMAL(15,2) DEFAULT 0"),
            (db_col + "_lotes", "SMALLINT DEFAULT 0"),
        ]:
            try:
                # First check if column already exists
                check_sql = (
                    "SELECT COUNT(*) AS cnt FROM information_schema.columns "
                    "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s"
                )
                result = db_manager.execute_query(check_sql, [table, col_name])
                if result and result[0]['cnt'] > 0:
                    table_updated = True  # Column already exists
                    continue
                
                # Column doesn't exist, add it
                sql = f"ALTER TABLE `{table}` ADD COLUMN `{col_name}` {col_type}"
                db_manager.execute_query(sql)
                table_updated = True
            except Exception as exc:
                msg = str(exc)
                # Ignore 'Duplicate column name' (1060) – already exists
                if "1060" in msg or "Duplicate column" in msg:
                    table_updated = True  # Column already existed
                else:
                    errors.append(f"{table}.{col_name}: {msg}")
        
        if table_updated and table not in updated_tables:
            updated_tables.append(table)

    if errors:
        return False, "\n".join(errors), updated_tables
    return True, f"Updated tables: {', '.join(updated_tables)}" if updated_tables else "No tables updated", updated_tables


def _remove_db_columns(db_col: str) -> tuple:
    """
    Remove columns from all report tables when a field is deleted.
    
    Removes:
        <db_col>        (amount column)
        <db_col>_lotes  (transaction count column)
    
    Returns (success: bool, message: str).
    """
    # All tables that might have the field
    tables = [
        "daily_reports", 
        "daily_reports_brand_a",
        "daily_transaction_tbl_brand_a",
        "PL_tbl_brand_a",
        "other_services_tbl_brand_a"
    ]
    
    errors = []
    removed_from = []

    if not db_manager.test_connection():
        return False, "Cannot connect to the database."

    for table in tables:
        # Check if the table exists
        try:
            exists = db_manager.execute_query(
                "SELECT COUNT(*) AS cnt FROM information_schema.tables "
                "WHERE table_schema = DATABASE() AND table_name = %s",
                [table]
            )
            if not exists or exists[0]['cnt'] == 0:
                continue  # Table doesn't exist
        except Exception:
            continue

        for col_name in [db_col, db_col + "_lotes"]:
            try:
                # Check if column exists before trying to drop
                col_exists = db_manager.execute_query(
                    "SELECT COUNT(*) AS cnt FROM information_schema.columns "
                    "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s",
                    [table, col_name]
                )
                if col_exists and col_exists[0]['cnt'] > 0:
                    sql = f"ALTER TABLE `{table}` DROP COLUMN `{col_name}`"
                    db_manager.execute_query(sql)
                    if table not in removed_from:
                        removed_from.append(table)
            except Exception as exc:
                errors.append(f"{table}.{col_name}: {str(exc)}")

    if errors:
        return False, "\n".join(errors)
    
    msg = f"Removed from: {', '.join(removed_from)}" if removed_from else "No columns found to remove"
    return True, msg


def _label_to_db_column(label: str) -> str:
    """Convert a human-readable label to a safe snake_case DB column name."""
    col = label.lower()
    col = re.sub(r"[^a-z0-9]+", "_", col)
    col = col.strip("_")
    return col


# ─────────────────────────────────────────────────────────────────────────────
class FieldManagerPage(QWidget):
    """The core 'add / remove fields' page inside the Super Admin Dashboard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = load_field_config()
        self._build_ui()

    # ── public ───────────────────────────────────────────────────────────────

    def reload_config(self):
        """Re-read the JSON file and refresh the field list."""
        self._config = load_field_config()
        self._refresh_field_list()

    def _sync_db_columns(self):
        """Sync all fields from config to database - ensures columns exist for ALL brands/sections."""
        synced_count = 0
        errors = []
        all_updated_tables = set()
        total_fields = 0
        
        # Iterate through all brands and sections
        for brand in ["Brand A", "Brand B"]:
            for section in ["debit", "credit"]:
                fields = self._config.get(brand, {}).get(section, [])
                for f in fields:
                    if len(f) >= 3:
                        total_fields += 1
                        db_col = f[2]
                        # Get report tables from field metadata
                        report_tables = []
                        if len(f) > 3 and isinstance(f[3], dict):
                            report_tables = f[3].get('reports', [])
                        
                        result = _ensure_db_columns(db_col, report_tables)
                        ok = result[0]
                        msg = result[1]
                        updated = result[2] if len(result) > 2 else []
                        
                        if ok:
                            synced_count += 1
                            all_updated_tables.update(updated)
                        else:
                            errors.append(f"{f[0]}: {msg}")
        
        if total_fields == 0:
            QMessageBox.information(self, "Sync", "No fields to sync.")
            return
        
        # Build display message
        table_display_names = {
            'daily_reports': 'Daily Reports',
            'daily_reports_brand_a': 'Daily Reports (Brand A)',
            'daily_transaction_tbl_brand_a': 'Daily Transaction',
            'PL_tbl_brand_a': 'P&L',
            'other_services_tbl_brand_a': 'Other Services'
        }
        updated_display = [table_display_names.get(t, t) for t in all_updated_tables]
        
        if errors:
            QMessageBox.warning(
                self, "Sync Completed with Errors",
                f"Synced {synced_count}/{total_fields} fields.\n\n"
                f"Errors:\n" + "\n".join(errors[:10])  # Limit errors shown
            )
        else:
            tables_msg = "\n• ".join(updated_display) if updated_display else "No new columns needed"
            QMessageBox.information(
                self, "Sync Complete",
                f"✅ All {synced_count} fields synced successfully!\n\n"
                f"Tables checked/updated:\n• {tables_msg}"
            )

    # ── private helpers ───────────────────────────────────────────────────────

    @property
    def _brand(self) -> str:
        return self._brand_combo.currentText()

    # Map display labels to config keys
    # In accounting: Credit = Cash Receipt (Rescate, Interest, etc.)
    #                Debit  = Cash Out (Empeno, etc.)
    _SECTION_DISPLAY_TO_KEY = {
        "Credit (Cash Receipt)": "debit",
        "Debit (Cash Out)": "credit",
    }

    @property
    def _section(self) -> str:
        display = self._section_combo.currentText()
        return self._SECTION_DISPLAY_TO_KEY.get(display, display.lower())

    @property
    def _section_display(self) -> str:
        return self._section_combo.currentText()

    def _fields(self) -> list:
        return self._config.get(self._brand, {}).get(self._section, [])

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(20, 20, 20, 20)

        # ── Page title ────────────────────────────────────────────────────────
        title = QLabel("⚙️  Cash-Flow Field Manager")
        title.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #2c3e50;"
        )
        root.addWidget(title)

        desc = QLabel(
            "Add or remove fields that appear in the client's Cash-Flow tab "
            "for each Brand and section.\n"
            "Changes are saved immediately and take effect the next time a "
            "client opens / switches brand."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #555; font-size: 11px;")
        root.addWidget(desc)

        filter_frame = QFrame()
        filter_frame.setStyleSheet(
            "QFrame { background: #ecf0f1; border-radius: 8px; padding: 8px; }"
        )
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setSpacing(15)

        filter_layout.addWidget(QLabel("Brand:"))
        self._brand_combo = QComboBox()
        self._brand_combo.addItems(["Brand A", "Brand B"])
        self._brand_combo.setMinimumWidth(120)
        self._brand_combo.currentTextChanged.connect(self._refresh_field_list)
        filter_layout.addWidget(self._brand_combo)

        filter_layout.addWidget(QLabel("Section:"))
        self._section_combo = QComboBox()
        self._section_combo.addItems(["Credit (Cash Receipt)", "Debit (Cash Out)"])
        self._section_combo.setMinimumWidth(100)
        self._section_combo.currentTextChanged.connect(self._refresh_field_list)
        filter_layout.addWidget(self._section_combo)

        self._field_count_label = QLabel("")
        self._field_count_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        filter_layout.addWidget(self._field_count_label)
        filter_layout.addStretch()

        root.addWidget(filter_frame)

        list_group = QGroupBox("Current Fields")
        list_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; font-size: 13px; color: #2c3e50;
                border: 2px solid #bdc3c7; border-radius: 8px;
                margin-top: 10px; padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 10px;
                padding: 0 8px; background-color: white;
            }
        """)
        list_vbox = QVBoxLayout(list_group)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setMinimumHeight(350)
        self._scroll_area.setStyleSheet("QScrollArea { border: none; }")

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setSpacing(4)
        self._list_layout.setContentsMargins(4, 4, 4, 4)
        self._list_layout.addStretch()

        self._scroll_area.setWidget(self._list_container)
        list_vbox.addWidget(self._scroll_area)
        root.addWidget(list_group)

        # ── Add new field row ─────────────────────────────────────────────────
        add_group = QGroupBox("➕ Add New Field")
        add_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; font-size: 13px; color: #27ae60;
                border: 2px solid #a9dfbf; border-radius: 8px;
                margin-top: 10px; padding-top: 15px;
                background-color: #f0fff4;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 10px;
                padding: 0 8px; background-color: #f0fff4;
            }
        """)
        add_vbox = QVBoxLayout(add_group)

        add_row = QHBoxLayout()
        add_row.setSpacing(10)

        name_label = QLabel("Field Name:")
        name_label.setStyleSheet("font-weight: bold;")
        add_row.addWidget(name_label)

        self._new_field_input = QLineEdit()
        self._new_field_input.setPlaceholderText(
            "e.g. 'New Remittance Fee'  (will be shown exactly as typed)"
        )
        self._new_field_input.setMinimumWidth(320)
        self._new_field_input.setFixedHeight(34)
        self._new_field_input.returnPressed.connect(self._add_field)
        add_row.addWidget(self._new_field_input, 1)

        add_btn = QPushButton("➕ Add Field")
        add_btn.setFixedHeight(34)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                border: none; border-radius: 6px;
                font-weight: bold; font-size: 12px; padding: 0 18px;
            }
            QPushButton:hover { background-color: #219a52; }
            QPushButton:pressed { background-color: #1a7a42; }
        """)
        add_btn.clicked.connect(self._add_field)
        add_row.addWidget(add_btn)

        add_vbox.addLayout(add_row)

   
        report_row = QHBoxLayout()
        report_row.setSpacing(15)
        
        report_label = QLabel("Add to reports:")
        report_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        report_row.addWidget(report_label)
        
        self._chk_daily_txn = QCheckBox("Daily Transaction")
        self._chk_daily_txn.setStyleSheet("font-size: 11px;")
        self._chk_daily_txn.setToolTip("Add field to Daily Transaction report table")
        report_row.addWidget(self._chk_daily_txn)
        
        self._chk_pnl = QCheckBox("P&&L")
        self._chk_pnl.setStyleSheet("font-size: 11px;")
        self._chk_pnl.setToolTip("Add field to Profit & Loss report table")
        report_row.addWidget(self._chk_pnl)
        
        self._chk_other_services = QCheckBox("Other Services")
        self._chk_other_services.setStyleSheet("font-size: 11px;")
        self._chk_other_services.setToolTip("Add field to Other Services report table")
        report_row.addWidget(self._chk_other_services)
        
        report_row.addStretch()
        add_vbox.addLayout(report_row)

        hint = QLabel(
            "The DB column name is derived automatically from the field name "
            "(spaces → underscores, special chars stripped). "
            "Check the reports where this field should appear."
        )
        hint.setStyleSheet("color: #888; font-size: 10px;")
        add_vbox.addWidget(hint)

        root.addWidget(add_group)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        self._reset_btn = QPushButton("Reload from File")
        self._reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12; color: white;
                border: none; border-radius: 6px;
                font-weight: bold; padding: 8px 18px;
            }
            QPushButton:hover { background-color: #d68910; }
        """)
        self._reset_btn.clicked.connect(self.reload_config)
        btn_row.addWidget(self._reset_btn)

        self._sync_btn = QPushButton("Sync DB Columns")
        self._sync_btn.setToolTip("Ensure all fields have their database columns created")
        self._sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white;
                border: none; border-radius: 6px;
                font-weight: bold; padding: 8px 18px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self._sync_btn.clicked.connect(self._sync_db_columns)
        btn_row.addWidget(self._sync_btn)

        root.addLayout(btn_row)

        self._refresh_field_list()

    def _refresh_field_list(self):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        fields = self._fields()
        self._field_count_label.setText(f"({len(fields)} fields)")

        if not fields:
            empty = QLabel("  No fields configured for this brand / section.")
            empty.setStyleSheet("color: #aaa; font-style: italic; padding: 10px;")
            self._list_layout.insertWidget(0, empty)
            return

        for idx, entry in enumerate(fields):
            label = entry[0]
            db_col = entry[2] if len(entry) >= 3 else _label_to_db_column(label)
            row_widget = self._make_field_row(idx, label, db_col)
            self._list_layout.insertWidget(idx, row_widget)

    def _make_field_row(self, idx: int, label: str, db_col: str) -> QWidget:
        row = QFrame()
        row.setFixedHeight(40)
        bg = "#ffffff" if idx % 2 == 0 else "#f8f9fa"
        row.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid #e9ecef;
                border-radius: 5px;
            }}
        """)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        num = QLabel(f"{idx + 1:02d}")
        num.setFixedWidth(26)
        num.setAlignment(Qt.AlignCenter)
        num.setStyleSheet(
            "font-size: 10px; color: #888; background: #e0e4e8; "
            "border-radius: 3px; padding: 2px;"
        )
        layout.addWidget(num)

        name_lbl = QLabel(label)
        name_lbl.setStyleSheet("font-weight: bold; font-size: 12px; color: #2c3e50;")
        layout.addWidget(name_lbl, 1)

        col_lbl = QLabel(f"→ {db_col}")
        col_lbl.setStyleSheet("font-size: 10px; color: #7f8c8d; font-family: monospace;")
        col_lbl.setMinimumWidth(200)
        layout.addWidget(col_lbl)

        up_btn = QPushButton("▲")
        up_btn.setFixedSize(28, 28)
        up_btn.setToolTip("Move field up")
        up_btn.setStyleSheet("""
            QPushButton {
                background: #d5d8dc; border: none; border-radius: 4px;
                font-size: 11px; font-weight: bold; color: #555;
            }
            QPushButton:hover { background: #aab7b8; }
            QPushButton:disabled { background: #ecf0f1; color: #ccc; }
        """)
        up_btn.setEnabled(idx > 0)
        up_btn.clicked.connect(lambda _, i=idx: self._move_field(i, -1))
        layout.addWidget(up_btn)

        down_btn = QPushButton("▼")
        down_btn.setFixedSize(28, 28)
        down_btn.setToolTip("Move field down")
        down_btn.setStyleSheet("""
            QPushButton {
                background: #d5d8dc; border: none; border-radius: 4px;
                font-size: 11px; font-weight: bold; color: #555;
            }
            QPushButton:hover { background: #aab7b8; }
            QPushButton:disabled { background: #ecf0f1; color: #ccc; }
        """)
        down_btn.setEnabled(idx < len(self._fields()) - 1)
        down_btn.clicked.connect(lambda _, i=idx: self._move_field(i, +1))
        layout.addWidget(down_btn)

        # Remove button
        rm_btn = QPushButton("🗑 Remove")
        rm_btn.setFixedHeight(28)
        rm_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; color: white;
                border: none; border-radius: 5px;
                font-size: 11px; font-weight: bold; padding: 0 12px;
            }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:pressed { background-color: #a93226; }
        """)
        rm_btn.clicked.connect(lambda _, lbl=label: self._remove_field(lbl))
        layout.addWidget(rm_btn)

        return row

    def _add_field(self):
        label = self._new_field_input.text().strip()
        if not label:
            QMessageBox.warning(self, "Empty Name", "Please enter a field name.")
            return

        fields = self._fields()
        if any(f[0].lower() == label.lower() for f in fields):
            QMessageBox.warning(
                self, "Duplicate",
                f"A field named '{label}' already exists in "
                f"{self._brand} → {self._section_display}."
            )
            return

        db_col = _label_to_db_column(label)
        if any((f[2] if len(f) >= 3 else _label_to_db_column(f[0])) == db_col
               for f in fields):
            QMessageBox.warning(
                self, "Column Collision",
                f"A field that maps to the DB column '{db_col}' already exists.\n"
                f"Please use a slightly different name to avoid conflicts."
            )
            return

        # Collect selected report tables
        report_tables = []
        if self._chk_daily_txn.isChecked():
            report_tables.append('daily_transaction')
        if self._chk_pnl.isChecked():
            report_tables.append('pnl')
        if self._chk_other_services.isChecked():
            report_tables.append('other_services')

        fields.append([label, f"Enter {label}", db_col, {"reports": report_tables}])
        if save_field_config(self._config):
            result = _ensure_db_columns(db_col, report_tables)
            ok = result[0]
            msg = result[1]
            updated_tables = result[2] if len(result) > 2 else []
            
            table_display_names = {
                'daily_reports': 'Daily Reports',
                'daily_reports_brand_a': 'Daily Reports (Brand A)',
                'daily_transaction_tbl_brand_a': 'Daily Transaction',
                'PL_tbl_brand_a': 'P&L',
                'other_services_tbl_brand_a': 'Other Services'
            }
            updated_display = [table_display_names.get(t, t) for t in updated_tables]
            tables_msg = f"\n\nDatabase tables updated:\n• " + "\n• ".join(updated_display) if updated_display else ""
            
            if ok:
                self._new_field_input.clear()
                self._chk_daily_txn.setChecked(False)
                self._chk_pnl.setChecked(False)
                self._chk_other_services.setChecked(False)
                self._refresh_field_list()
                self._scroll_to_bottom()
                QMessageBox.information(
                    self, "Field Added",
                    f"✅  Field '{label}' added successfully.\n"
                    f"Database columns '{db_col}' and '{db_col}_lotes' created.{tables_msg}"
                )
            else:
                self._new_field_input.clear()
                self._chk_daily_txn.setChecked(False)
                self._chk_pnl.setChecked(False)
                self._chk_other_services.setChecked(False)
                self._refresh_field_list()
                self._scroll_to_bottom()
                QMessageBox.warning(
                    self, "Field Added (DB Warning)",
                    f"✅  Field '{label}' saved to config.\n\n"
                    f"⚠️  Could not auto-create DB columns:\n{msg}\n\n"
                    f"Please click 'Sync DB Columns' button to retry."
                )
        else:
            QMessageBox.critical(self, "Save Error", "Could not write field_config.json.")

    def _remove_field(self, label: str):
        # Find the db_col for this field
        fields = self._fields()
        db_col = None
        for f in fields:
            if f[0] == label:
                db_col = f[2] if len(f) >= 3 else _label_to_db_column(label)
                break
        
        reply = QMessageBox.question(
            self,
            "Confirm Remove",
            f"Remove field  '{label}'  from  {self._brand} → {self._section_display}?\n\n"
            f"⚠️  This will ALSO delete the database columns:\n"
            f"    • {db_col}\n"
            f"    • {db_col}_lotes\n\n"
            f"Existing data in these columns will be PERMANENTLY LOST!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return


        self._config[self._brand][self._section] = [
            f for f in fields if f[0] != label
        ]
        
        if save_field_config(self._config):

            if db_col:
                ok, msg = _remove_db_columns(db_col)
                if ok:
                    QMessageBox.information(
                        self, "Field Removed",
                        f"✅  Field '{label}' removed from config.\n"
                        f"Database columns removed: {msg}"
                    )
                else:
                    QMessageBox.warning(
                        self, "Field Removed (DB Warning)",
                        f"Field '{label}' removed from config.\n\n"
                        f"Could not remove some DB columns:\n{msg}"
                    )
            self._refresh_field_list()
        else:
            QMessageBox.critical(self, "Save Error", "Could not write field_config.json.")

    def _move_field(self, idx: int, direction: int):
        """Move a field up (-1) or down (+1) in the list."""
        fields = self._fields()
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(fields):
            return
        fields[idx], fields[new_idx] = fields[new_idx], fields[idx]
        if save_field_config(self._config):
            self._refresh_field_list()
        else:
            QMessageBox.critical(self, "Save Error", "Could not write field_config.json.")

    def _scroll_to_bottom(self):
        sb = self._scroll_area.verticalScrollBar()
        QTimer.singleShot(50, lambda: sb.setValue(sb.maximum()))


class SuperAdminDashboard(QWidget):
    """Top-level window shown when a 'super_admin' user logs in."""

    logout_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Super Admin Dashboard – Cash Management System")
        self.setMinimumSize(1050, 700)
        self.showMaximized()

        self.session = SessionManager(inactivity_timeout=1800)
        self._session_timer = QTimer(self)
        self._session_timer.timeout.connect(self._check_session_timeout)
        self._session_timer.start(60000)

        self._build_ui()

        if AUTO_UPDATE_ENABLED and check_update_success:
            check_update_success(parent=self)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        main_layout.addWidget(self._build_header())

        self._main_tabs = QTabWidget()
        self._main_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d5d8dc;
                border-radius: 6px;
                background: white;
            }
            QTabBar::tab {
                background: #4a235a; color: #e8daef;
                padding: 10px 22px; font-weight: bold; font-size: 12px;
                border: none; border-top-left-radius: 6px;
                border-top-right-radius: 6px; margin-right: 2px;
            }
            QTabBar::tab:selected { background: #884ea0; color: white; }
            QTabBar::tab:hover   { background: #6c3483; }
        """)

        # Tab 0 – Super Admin (Field Manager + User Management)
        sa_widget = QWidget()
        sa_layout = QVBoxLayout(sa_widget)
        sa_layout.setContentsMargins(0, 5, 0, 0)
        sa_layout.setSpacing(8)
        sa_layout.addWidget(self._build_nav())

        self._stack = QStackedWidget()
        self._field_manager_page = FieldManagerPage()
        self._user_mgmt_page = self._build_user_mgmt_placeholder()
        self._stack.addWidget(self._field_manager_page)   # index 0
        self._stack.addWidget(self._user_mgmt_page)       # index 1
        sa_layout.addWidget(self._stack, 1)
        self._main_tabs.addTab(sa_widget, "🛠️ Super Admin")

        # Tab 1 – Admin Brand A (lazy-loaded)
        self._admin_a_container = QWidget()
        QVBoxLayout(self._admin_a_container)
        self._admin_a_loaded = False
        self._main_tabs.addTab(self._admin_a_container, "📊 Admin Brand A")

        # Tab 2 – Admin Brand B (lazy-loaded)
        self._admin_b_container = QWidget()
        QVBoxLayout(self._admin_b_container)
        self._admin_b_loaded = False
        self._main_tabs.addTab(self._admin_b_container, "📊 Admin Brand B")

        # Tab 3 – Client View (with branch selector)
        self._client_container = self._build_client_tab()
        self._main_tabs.addTab(self._client_container, "👤 Client View")

        self._main_tabs.currentChanged.connect(self._on_main_tab_changed)
        main_layout.addWidget(self._main_tabs, 1)

    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6c3483, stop:1 #884ea0
                );
                border-radius: 8px;
            }
            QLabel { background: transparent; border: none; }
        """)
        frame.setFixedHeight(70)
        h = QHBoxLayout(frame)
        h.setContentsMargins(20, 0, 16, 0)

        crown = QLabel("👑 Super Admin Dashboard")
        crown.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: white;"
        )
        h.addWidget(crown)
        h.addStretch()

        if AUTO_UPDATE_ENABLED:
            ver_btn = QPushButton(f"ℹ️ v{__version__}")
            ver_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1abc9c; color: white;
                    border: none; padding: 8px 16px; border-radius: 6px;
                    font-weight: bold; font-size: 11px;
                }
                QPushButton:hover { background-color: #17a589; }
            """)
            ver_btn.setToolTip("Check for updates")
            ver_btn.clicked.connect(self._check_updates)
            h.addWidget(ver_btn)

        ping_btn = QPushButton("📡 Ping Monitor")
        ping_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad; color: white;
                border: none; padding: 10px 16px; border-radius: 6px;
                font-weight: bold; font-size: 11px; min-width: 110px;
            }
            QPushButton:hover { background-color: #9b59b6; }
            QPushButton:pressed { background-color: #7d3c98; }
        """)
        ping_btn.setToolTip("View user connection / ping logs")
        ping_btn.clicked.connect(self._open_ping_monitor)
        h.addWidget(ping_btn)

        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; color: white;
                border: none; padding: 10px 20px; border-radius: 6px;
                font-weight: bold; font-size: 12px; min-width: 100px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        logout_btn.clicked.connect(self._handle_logout)
        h.addWidget(logout_btn)
        return frame

    def _build_nav(self) -> QFrame:
        nav = QFrame()
        nav.setObjectName("navBar")
        nav.setStyleSheet("""
            QFrame#navBar {
                background-color: #4a235a;
                border-radius: 8px;
                padding: 5px;
            }
            QFrame#navBar QPushButton {
                background-color: #4a235a;
                border: 2px solid transparent;
                color: #e8daef;
                font-size: 12px; font-weight: bold;
                padding: 10px 15px; border-radius: 6px;
            }
            QFrame#navBar QPushButton:hover { background-color: #884ea0; }
            QFrame#navBar QPushButton:checked {
                background-color: #884ea0;
                border-color: #d2b4de;
            }
        """)
        layout = QHBoxLayout(nav)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)

        self._field_btn = QPushButton("⚙️ Field Manager")
        self._field_btn.setCheckable(True)
        self._field_btn.setChecked(True)
        self._field_btn.clicked.connect(lambda: self._switch_view(0, self._field_btn))

        self._user_btn = QPushButton("👥 User Management")
        self._user_btn.setCheckable(True)
        self._user_btn.clicked.connect(lambda: self._switch_view(1, self._user_btn))

        layout.addWidget(self._field_btn)
        layout.addWidget(self._user_btn)
        layout.addStretch()
        return nav

    def _build_user_mgmt_placeholder(self) -> QWidget:
        """Try to load the real UserManagementPage; fall back to a placeholder."""
        try:
            from user_management_page import UserManagementPage
            return UserManagementPage(is_super_admin=True)
        except Exception as exc:
            print(f"[SuperAdmin] Could not load UserManagementPage: {exc}")
            placeholder = QWidget()
            lbl = QLabel("👥 User Management\n\n(Module not available)")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 16px; color: #888;")
            QVBoxLayout(placeholder).addWidget(lbl)
            return placeholder

    # ── slots ─────────────────────────────────────────────────────────────────

    def _switch_view(self, index: int, active_btn: QPushButton):
        self._stack.setCurrentIndex(index)
        for btn in (self._field_btn, self._user_btn):
            btn.setChecked(btn is active_btn)

    # ── Main-tab lazy loading ─────────────────────────────────────────────

    def _on_main_tab_changed(self, index):
        """Lazy-load admin / client dashboards on first visit."""
        if index == 1 and not self._admin_a_loaded:
            self._load_admin_tab(1, account_type=1)
        elif index == 2 and not self._admin_b_loaded:
            self._load_admin_tab(2, account_type=2)

    def _load_admin_tab(self, tab_index, account_type):
        """Instantiate an AdminDashboard and embed it in the given tab."""
        try:
            from admin_dashboard import AdminDashboard
            dashboard = AdminDashboard(account_type=account_type)
            dashboard._session_timer.stop()
            dashboard.handle_logout = lambda: QMessageBox.information(
                dashboard, "Info",
                "Use the main Super Admin logout button to logout."
            )
            container = self._admin_a_container if tab_index == 1 \
                else self._admin_b_container
            container.layout().addWidget(dashboard)
            if tab_index == 1:
                self._admin_a_loaded = True
            else:
                self._admin_b_loaded = True
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Failed to load Admin dashboard:\n{e}"
            )

    # ── Client View tab ───────────────────────────────────────────────────

    def _build_client_tab(self):
        """Build the Client View tab with a branch selector."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Branch selector bar
        selector = QFrame()
        selector.setStyleSheet(
            "QFrame { background: #f8f9fa; border-radius: 6px; padding: 10px; }"
        )
        sel_lay = QHBoxLayout(selector)
        sel_lay.setSpacing(10)

        sel_lay.addWidget(QLabel("🏢 Select Branch:"))
        self._client_branch_combo = QComboBox()
        self._client_branch_combo.setMinimumWidth(300)
        try:
            rows = db_manager.execute_query(
                "SELECT b.name, c.name AS corp "
                "FROM branches b "
                "LEFT JOIN corporations c ON b.corporation_id = c.id "
                "WHERE b.is_registered = 1 ORDER BY c.name, b.name"
            )
            if rows:
                for r in rows:
                    display = f"{r['name']}  ({r['corp']})" if r.get('corp') else r['name']
                    self._client_branch_combo.addItem(display, r['name'])
        except Exception:
            pass
        sel_lay.addWidget(self._client_branch_combo)

        load_btn = QPushButton("🔄 Load Client View")
        load_btn.setStyleSheet(
            "QPushButton { background: #3498db; color: white; padding: 8px 20px;"
            " border: none; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        load_btn.clicked.connect(self._load_client_dashboard)
        sel_lay.addWidget(load_btn)
        sel_lay.addStretch()
        layout.addWidget(selector)

        # Container for the client dashboard widget
        self._client_dash_holder = QVBoxLayout()
        layout.addLayout(self._client_dash_holder, 1)
        return widget

    def _load_client_dashboard(self):
        """Create / recreate a ClientDashboard for the chosen branch."""
        branch = self._client_branch_combo.currentData()
        if not branch:
            QMessageBox.warning(self, "No Branch", "Please select a branch first.")
            return

        # Look up corporation
        try:
            res = db_manager.execute_query(
                "SELECT c.name FROM branches b "
                "LEFT JOIN corporations c ON b.corporation_id = c.id "
                "WHERE b.name = %s", [branch]
            )
            corporation = res[0]['name'] if res else ""
        except Exception:
            corporation = ""

        # Remove previous dashboard if any
        while self._client_dash_holder.count():
            item = self._client_dash_holder.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            from Client.client_dashboard import ClientDashboard
            dash = ClientDashboard(
                username="super_admin",
                branch=branch,
                corporation=corporation,
                db_manager=db_manager,
                offline_mode=False,
            )
            dash._session_timer.stop()
            dash.handle_logout = lambda: QMessageBox.information(
                dash, "Info",
                "Use the main Super Admin logout button to logout."
            )
            self._client_dash_holder.addWidget(dash)
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Failed to load Client dashboard:\n{e}"
            )

    def _open_ping_monitor(self):
        window = PingMonitorWindow(db_manager, parent=self)
        window.exec_()

    def _handle_logout(self):
        reply = QMessageBox.question(
            self, "Confirm Logout", "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.session.logout()
            self.logout_requested.emit()
            self.close()

    def _check_session_timeout(self):
        if self.session.check_timeout():
            self._session_timer.stop()
            QMessageBox.warning(
                self, "Session Expired",
                "Your session has expired due to inactivity.\nPlease log in again."
            )
            self.logout_requested.emit()
            self.close()

    def _check_updates(self):
        if AUTO_UPDATE_ENABLED:
            check_for_updates(parent=self, silent=False)

    # ── Qt event overrides ────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        self.session.update_activity()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self.session.update_activity()
        super().keyPressEvent(event)
