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
    QComboBox, QSizePolicy, QStackedWidget, QFormLayout, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from db_connect_pooled import db_manager
from security import SessionManager

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
def load_field_config() -> dict:
    """Load field_config.json.  Returns default skeleton on any error."""
    try:
        with open(FIELD_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # Ensure expected structure
        for brand in ("Brand A", "Brand B"):
            cfg.setdefault(brand, {})
            cfg[brand].setdefault("debit", [])
            cfg[brand].setdefault("credit", [])
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
    """Persist the config dict to disk.  Returns True on success."""
    try:
        with open(FIELD_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception as exc:
        print(f"[SuperAdmin] Failed to save field config: {exc}")
        return False


def _ensure_db_columns(db_col: str) -> tuple:
    """
    Make sure both `daily_reports` and `daily_reports_brand_a` tables have
    the two columns required for a new field::

        <db_col>        DECIMAL(15,2) DEFAULT 0   (amount)
        <db_col>_lotes  SMALLINT DEFAULT 0        (transaction count)

    Returns (success: bool, message: str).
    Skips silently if the column already exists (MySQL's IF NOT EXISTS).
    """
    tables = ["daily_reports", "daily_reports_brand_a"]
    errors = []

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

        for col_name, col_type in [
            (db_col,           "DECIMAL(15,2) DEFAULT 0"),
            (db_col + "_lotes", "SMALLINT DEFAULT 0"),
        ]:
            try:
                # Use ALTER TABLE … ADD COLUMN IF NOT EXISTS (MySQL 8+)
                # For older MySQL, catch the 'Duplicate column' error
                sql = (
                    f"ALTER TABLE `{table}` "
                    f"ADD COLUMN IF NOT EXISTS `{col_name}` {col_type}"
                )
                db_manager.execute_query(sql)
            except Exception as exc:
                msg = str(exc)
                # Ignore 'Duplicate column name' (1060) – already exists
                if "1060" in msg or "Duplicate column" in msg:
                    pass
                else:
                    errors.append(f"{table}.{col_name}: {msg}")

    if errors:
        return False, "\n".join(errors)
    return True, "OK"



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

    # ── private helpers ───────────────────────────────────────────────────────

    @property
    def _brand(self) -> str:
        return self._brand_combo.currentText()

    @property
    def _section(self) -> str:
        return self._section_combo.currentText().lower()  # "debit" | "credit"

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

        # ── Filter row ────────────────────────────────────────────────────────
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
        self._section_combo.addItems(["Debit", "Credit"])
        self._section_combo.setMinimumWidth(100)
        self._section_combo.currentTextChanged.connect(self._refresh_field_list)
        filter_layout.addWidget(self._section_combo)

        self._field_count_label = QLabel("")
        self._field_count_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        filter_layout.addWidget(self._field_count_label)
        filter_layout.addStretch()

        root.addWidget(filter_frame)

        # ── Field list ────────────────────────────────────────────────────────
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

        hint = QLabel(
            "💡  The DB column name is derived automatically from the field name "
            "(spaces → underscores, special chars stripped)."
        )
        hint.setStyleSheet("color: #888; font-size: 10px;")
        add_vbox.addWidget(hint)

        root.addWidget(add_group)

        # ── Bottom action buttons ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        self._reset_btn = QPushButton("🔄 Reload from File")
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

        root.addLayout(btn_row)

        # ── Populate initial list ─────────────────────────────────────────────
        self._refresh_field_list()

    # ── slot implementations ──────────────────────────────────────────────────

    def _refresh_field_list(self):
        """Clear and rebuild the scrollable field list for the current filter."""
        # Remove all widgets except the trailing stretch
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

        # Index badge
        num = QLabel(f"{idx + 1:02d}")
        num.setFixedWidth(26)
        num.setAlignment(Qt.AlignCenter)
        num.setStyleSheet(
            "font-size: 10px; color: #888; background: #e0e4e8; "
            "border-radius: 3px; padding: 2px;"
        )
        layout.addWidget(num)

        # Field label
        name_lbl = QLabel(label)
        name_lbl.setStyleSheet("font-weight: bold; font-size: 12px; color: #2c3e50;")
        layout.addWidget(name_lbl, 1)

        # DB column indicator
        col_lbl = QLabel(f"→ {db_col}")
        col_lbl.setStyleSheet("font-size: 10px; color: #7f8c8d; font-family: monospace;")
        col_lbl.setMinimumWidth(200)
        layout.addWidget(col_lbl)

        # Move Up / Down
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
        # Duplicate check (case-insensitive)
        if any(f[0].lower() == label.lower() for f in fields):
            QMessageBox.warning(
                self, "Duplicate",
                f"A field named '{label}' already exists in "
                f"{self._brand} → {self._section.title()}."
            )
            return

        db_col = _label_to_db_column(label)
        # Check DB column collision
        if any((f[2] if len(f) >= 3 else _label_to_db_column(f[0])) == db_col
               for f in fields):
            QMessageBox.warning(
                self, "Column Collision",
                f"A field that maps to the DB column '{db_col}' already exists.\n"
                f"Please use a slightly different name to avoid conflicts."
            )
            return

        fields.append([label, f"Enter {label}", db_col])
        if save_field_config(self._config):
            # ── Auto-create the columns in the database ───────────────────
            ok, msg = _ensure_db_columns(db_col)
            if ok:
                self._new_field_input.clear()
                self._refresh_field_list()
                self._scroll_to_bottom()
                QMessageBox.information(
                    self, "Field Added",
                    f"✅  Field '{label}' added successfully.\n"
                    f"Database columns '{db_col}' and '{db_col}_lotes' "
                    f"are ready (or already existed)."
                )
            else:
                self._new_field_input.clear()
                self._refresh_field_list()
                self._scroll_to_bottom()
                QMessageBox.warning(
                    self, "Field Added (DB Warning)",
                    f"✅  Field '{label}' saved to config.\n\n"
                    f"⚠️  Could not auto-create DB columns:\n{msg}\n\n"
                    f"Please run manually:\n"
                    f"  ALTER TABLE daily_reports "
                    f"ADD COLUMN `{db_col}` DECIMAL(15,2) DEFAULT 0;\n"
                    f"  ALTER TABLE daily_reports "
                    f"ADD COLUMN `{db_col}_lotes` SMALLINT DEFAULT 0;"
                )
        else:
            QMessageBox.critical(self, "Save Error", "Could not write field_config.json.")

    def _remove_field(self, label: str):
        reply = QMessageBox.question(
            self,
            "Confirm Remove",
            f"Remove field  '{label}'  from  {self._brand} → {self._section.title()}?\n\n"
            "⚠️  This does NOT delete existing data in the database — "
            "the column will simply no longer be shown in the form.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        fields = self._fields()
        self._config[self._brand][self._section] = [
            f for f in fields if f[0] != label
        ]
        if save_field_config(self._config):
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


# ─────────────────────────────────────────────────────────────────────────────
class SuperAdminDashboard(QWidget):
    """Top-level window shown when a 'super_admin' user logs in."""

    logout_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Super Admin Dashboard – Cash Management System")
        self.setMinimumSize(1050, 700)
        self.showMaximized()

        # Session management – 30-minute inactivity timeout
        self.session = SessionManager(inactivity_timeout=1800)
        self._session_timer = QTimer(self)
        self._session_timer.timeout.connect(self._check_session_timeout)
        self._session_timer.start(60000)

        self._build_ui()

        if AUTO_UPDATE_ENABLED and check_update_success:
            check_update_success(parent=self)

    # ── build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        main_layout.addWidget(self._build_header())
        main_layout.addWidget(self._build_nav())

        # Stacked content
        self._stack = QStackedWidget()
        self._field_manager_page = FieldManagerPage()
        self._user_mgmt_page = self._build_user_mgmt_placeholder()

        self._stack.addWidget(self._field_manager_page)   # index 0
        self._stack.addWidget(self._user_mgmt_page)       # index 1

        main_layout.addWidget(self._stack, 1)

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
            return UserManagementPage()
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
