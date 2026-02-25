import json
import os
import re

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QScrollArea, QFrame
)
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtCore import Qt

# ── field-config helpers (shared with super_admin_dashboard) ──────────────────
import sys as _sys

def _get_config_dir() -> str:
    """Return directory containing field_config.json.
    Works in both dev mode and PyInstaller frozen builds."""
    if getattr(_sys, 'frozen', False):
        # Running as a PyInstaller one-file exe — config lives next to the exe
        return os.path.dirname(_sys.executable)
    # Dev mode: two levels up from Client/cash_flow_tab.py → project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_BASE_DIR = _get_config_dir()
FIELD_CONFIG_PATH = os.path.join(_BASE_DIR, "field_config.json")


def _load_field_config() -> dict:
    """Load field_config.json.  Returns an empty structure on any error."""
    try:
        with open(FIELD_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"Brand A": {"debit": [], "credit": []},
                "Brand B": {"debit": [], "credit": []}}


def _sanitize_column(name: str) -> str:
    col = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return col


class CashFlowTab(QWidget):
    def __init__(self, parent, brand_name="Brand A"):
        super().__init__()
        self.parent = parent
        self.brand_name = brand_name  # Fixed brand for this tab instance

        # Storage for inputs
        self.debit_inputs = {}
        self.credit_inputs = {}
        self.debit_lotes_inputs = {}
        self.credit_lotes_inputs = {}

        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)

        # Build UI for this brand
        self.setup_ui()

    def setup_ui(self):
        """Setup UI based on current brand"""
        brand_color = "#3B82F6" if self.brand_name == "Brand A" else "#8B5CF6"
        brand_color_light = "#EFF6FF" if self.brand_name == "Brand A" else "#F5F3FF"

        # === Debit Section (Cash Outflow) ===
        debit_scroll = QScrollArea()
        debit_scroll.setWidgetResizable(True)

        debit_box = QGroupBox("")
        debit_box.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                margin-top: 18px;
                padding: 18px 16px 14px 16px;
            }}
            QGroupBox::title {{
                color: #EF4444;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 1.2px;
                padding: 2px 10px;
                background-color: #FFFFFF;
                border-radius: 4px;
            }}
        """)
        debit_form = QFormLayout()
        debit_form.setSpacing(10)
        debit_form.setContentsMargins(16, 24, 16, 16)

        debit_fields = self.get_debit_fields()
        self.debit_inputs = self.build_input_group(debit_form, debit_fields, is_debit=True)

        debit_form.addRow(self.parent.create_separator(), QLabel(""))
        self.debit_total_display = self.parent.create_display_field("0.00")
        self.debit_total_display.setStyleSheet(
            "font-weight: 800; font-size: 14px; color: #EF4444; "
            "background-color: #FEF2F2; border: 1px solid #FECACA; "
            "border-radius: 8px; padding: 8px 12px;"
        )
        total_label = QLabel("Total Cash In:")
        total_label.setStyleSheet("font-weight: 700; color: #EF4444; font-size: 12px;")
        debit_form.addRow(total_label, self.debit_total_display)

        debit_box.setLayout(debit_form)
        debit_scroll.setWidget(debit_box)

        # === Credit Section (Cash Inflow) ===
        credit_scroll = QScrollArea()
        credit_scroll.setWidgetResizable(True)

        credit_box = QGroupBox("")
        credit_box.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                margin-top: 18px;
                padding: 18px 16px 14px 16px;
            }}
            QGroupBox::title {{
                color: #22C55E;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 1.2px;
                padding: 2px 10px;
                background-color: #FFFFFF;
                border-radius: 4px;
            }}
        """)
        credit_form = QFormLayout()
        credit_form.setSpacing(10)
        credit_form.setContentsMargins(16, 24, 16, 16)

        credit_fields = self.get_credit_fields()
        self.credit_inputs = self.build_input_group(credit_form, credit_fields, is_debit=False)

        credit_form.addRow(self.parent.create_separator(), QLabel(""))
        self.credit_total_display = self.parent.create_display_field("0.00")
        self.credit_total_display.setStyleSheet(
            "font-weight: 800; font-size: 14px; color: #22C55E; "
            "background-color: #F0FDF4; border: 1px solid #BBF7D0; "
            "border-radius: 8px; padding: 8px 12px;"
        )
        total_label = QLabel("Total Cash Out:")
        total_label.setStyleSheet("font-weight: 700; color: #22C55E; font-size: 12px;")
        credit_form.addRow(total_label, self.credit_total_display)

        credit_box.setLayout(credit_form)
        credit_scroll.setWidget(credit_box)

        self.main_layout.addWidget(debit_scroll)
        self.main_layout.addWidget(credit_scroll)

    def get_debit_fields(self):
        """Load debit fields for this brand from field_config.json."""
        cfg = _load_field_config()
        entries = cfg.get(self.brand_name, {}).get("debit", [])
        if entries:
            return [(e[0], e[1] if len(e) >= 2 else f"Enter {e[0]}") for e in entries]
        # Fallback – empty list shows nothing rather than crashing
        return []

    def get_credit_fields(self):
        """Load credit fields for this brand from field_config.json."""
        cfg = _load_field_config()
        entries = cfg.get(self.brand_name, {}).get("credit", [])
        if entries:
            return [(e[0], e[1] if len(e) >= 2 else f"Enter {e[0]}") for e in entries]
        return []

    def build_input_group(self, form_layout, fields, is_debit=True):
        """Build input group for fields with lotes input"""
        inputs = {}
        lotes_inputs = self.debit_lotes_inputs if is_debit else self.credit_lotes_inputs

        for label_text, placeholder in fields:
            amount_field = self.create_money_input(placeholder)
            lotes_field = self.create_lotes_input()

            container = QWidget()
            container.setContentsMargins(0, 0, 0, 0)
            row_layout = QHBoxLayout(container)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            row_layout.addWidget(amount_field, 1)

            lotes_lbl = QLabel("Lotes:")
            lotes_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #94A3B8;")
            row_layout.addWidget(lotes_lbl, 0)
            row_layout.addWidget(lotes_field, 0)

            label = QLabel(label_text + ":")
            label.setStyleSheet("font-size: 12px; font-weight: 600; color: #334155;")
            form_layout.addRow(label, container)

            inputs[label_text] = amount_field
            lotes_inputs[label_text] = lotes_field

        return inputs

    def create_money_input(self, placeholder=""):
        """Create money input field"""
        field = QLineEdit()
        field.setValidator(QDoubleValidator(0.0, 1e12, 2))
        field.setPlaceholderText(placeholder)
        field.textChanged.connect(self.parent.recalculate_all)
        return field

    def create_lotes_input(self, placeholder="0"):
        """Create lotes (transaction count) input field"""
        field = QLineEdit()
        field.setValidator(QIntValidator(0, 999999))
        field.setPlaceholderText(placeholder)
        field.setMaximumWidth(72)
        field.setStyleSheet(
            "background-color: #F8FAFC; border: 1px solid #E2E8F0; "
            "border-radius: 6px; padding: 6px 8px; font-size: 12px; "
            "color: #64748B; font-weight: 600; min-height: 30px; min-width: 50px;"
        )
        field.textChanged.connect(self.parent.recalculate_all)
        return field

    def get_debit_total(self):
        return self.parent.get_total_amount(self.debit_inputs)

    def get_credit_total(self):
        return self.parent.get_total_amount(self.credit_inputs)

    def update_totals(self, beginning, debit_total, credit_total):
        self.total_cash_in = beginning + debit_total
        self.debit_total_display.setText(f"{self.total_cash_in:.2f}")
        self.credit_total_display.setText(f"{credit_total:.2f}")

    @staticmethod
    def _sanitize_column(name: str) -> str:
        col = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
        return col

    def _build_column_mapping(self) -> dict:
        """Build a label→db_column dict from this brand's config entries."""
        cfg = _load_field_config()
        brand_cfg = cfg.get(self.brand_name, {})
        mapping = {}
        for section in ("debit", "credit"):
            for entry in brand_cfg.get(section, []):
                label = entry[0]
                col   = entry[2] if len(entry) >= 3 else _sanitize_column(label)
                mapping[label] = col
        return mapping

    def field_name_to_db_column(self, field_name):
        """Convert field label to DB column name using config, then safe fallback."""

        mapping = self._build_column_mapping()

        if field_name in mapping:
            return mapping[field_name]

        # Safe fallback — no dots, parens, or special chars will reach SQL
        col = self._sanitize_column(field_name)
        print(f"[WARN] field_name_to_db_column: '{field_name}' not in config mapping, "
              f"using sanitized fallback '{col}'")
        return col

    def get_data(self):
        """Get all data from cash flow tab"""
        debit_values = {}
        for k, v in self.debit_inputs.items():
            value = float(v.text().strip()) if v.text().strip() else 0
            db_column = self.field_name_to_db_column(k)
            debit_values[db_column] = value
            lotes_text = self.debit_lotes_inputs[k].text().strip()
            debit_values[db_column + "_lotes"] = int(lotes_text) if lotes_text else 0

        credit_values = {}
        for k, v in self.credit_inputs.items():
            value = float(v.text().strip()) if v.text().strip() else 0
            db_column = self.field_name_to_db_column(k)
            credit_values[db_column] = value
            lotes_text = self.credit_lotes_inputs[k].text().strip()
            credit_values[db_column + "_lotes"] = int(lotes_text) if lotes_text else 0

        return {'debit': debit_values, 'credit': credit_values}

    def clear_fields(self):
        """Clear all input fields"""
        for field in list(self.debit_inputs.values()) + list(self.debit_lotes_inputs.values()) \
                     + list(self.credit_inputs.values()) + list(self.credit_lotes_inputs.values()):
            field.clear()

    def get_raw_field_values(self) -> dict:
        """Return {label: {amount, lotes}} for all fields (used by draft save)."""
        out = {}
        for label, widget in self.debit_inputs.items():
            lotes_w = self.debit_lotes_inputs.get(label)
            out[f"debit::{label}"] = {
                "amount": widget.text(),
                "lotes": lotes_w.text() if lotes_w else ""
            }
        for label, widget in self.credit_inputs.items():
            lotes_w = self.credit_lotes_inputs.get(label)
            out[f"credit::{label}"] = {
                "amount": widget.text(),
                "lotes": lotes_w.text() if lotes_w else ""
            }
        return out

    def set_raw_field_values(self, data: dict):
        """Restore field values from draft data dict."""
        for key, val in data.items():
            section, label = key.split("::", 1)
            if section == "debit":
                widget = self.debit_inputs.get(label)
                lotes_w = self.debit_lotes_inputs.get(label)
            else:
                widget = self.credit_inputs.get(label)
                lotes_w = self.credit_lotes_inputs.get(label)
            if widget:
                widget.blockSignals(True)
                widget.setText(val.get("amount", ""))
                widget.blockSignals(False)
            if lotes_w:
                lotes_w.blockSignals(True)
                lotes_w.setText(val.get("lotes", ""))
                lotes_w.blockSignals(False)
        self.parent.recalculate_all()

    def set_enabled(self, enabled):
        """Enable or disable all inputs"""
        for field in list(self.debit_inputs.values()) + list(self.debit_lotes_inputs.values()) \
                     + list(self.credit_inputs.values()) + list(self.credit_lotes_inputs.values()):
            field.setEnabled(enabled)