"""
PalawanPayableTab
-----------------
A tab widget for Palawan Payable data entry (Brand A).
Provides data-entry for:
  - PALAWAN SEND-OUT      : Lotes, Principal, SC, Commission, TOTAL
  - PALAWAN PAY-OUT       : Lotes, Principal, SC, Commission, TOTAL
  - PALAWAN INTERNATIONAL : Lotes, Principal, SC, Commission, TOTAL

Data is saved to `payable_tbl_brand_a` and flows into payable_page.py.
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QPushButton, QScrollArea, QFrame,
    QSizePolicy, QMessageBox
)
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtCore import Qt
import logging

from Client.ui_scaling import _sz

logger = logging.getLogger(__name__)

_SLATE_50  = "#F8FAFC"
_SLATE_100 = "#F1F5F9"
_SLATE_200 = "#E2E8F0"
_SLATE_700 = "#334155"
_SLATE_800 = "#1E293B"
_WHITE     = "#FFFFFF"

_SO_COLOR   = "#0EA5E9"   # sky-500
_PO_COLOR   = "#10B981"   # emerald-500
_INT_COLOR  = "#8B5CF6"   # violet-500
_SAVE_COLOR = "#0F172A"
_SAVE_HOVER = "#1E293B"


class PalawanPayableTab(QWidget):
    """Tab widget for Palawan Payable data entry (Brand A)."""

    def __init__(self, parent_dashboard):
        super().__init__()
        self._dashboard = parent_dashboard
        self._setup_ui()

    # ──────────────────────────────────────────────────────────────────────
    # UI BUILD
    # ──────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(_sz(12), _sz(12), _sz(12), _sz(12))
        outer.setSpacing(_sz(10))

        # Scroll area so it works on smaller screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        inner = QWidget()
        inner.setStyleSheet(f"background-color: {_WHITE};")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(_sz(12), _sz(10), _sz(12), _sz(10))
        inner_layout.setSpacing(_sz(10))

        # Title
        title = QLabel("PALAWAN PAYABLE — BRAND A")
        title.setStyleSheet(
            f"color: {_SLATE_800}; font-size: {_sz(14)}px; font-weight: 800; "
            f"letter-spacing: 1.5px; background: transparent;"
        )
        inner_layout.addWidget(title)

        # Three section groups side by side
        sections_row = QHBoxLayout()
        sections_row.setSpacing(_sz(10))

        self._so_group,  self._so_fields  = self._make_section("PALAWAN SEND-OUT",       _SO_COLOR)
        self._po_group,  self._po_fields  = self._make_section("PALAWAN PAY-OUT",         _PO_COLOR)
        self._int_group, self._int_fields = self._make_section("PALAWAN INTERNATIONAL",   _INT_COLOR)

        sections_row.addWidget(self._so_group)
        sections_row.addWidget(self._po_group)
        sections_row.addWidget(self._int_group)
        inner_layout.addLayout(sections_row)

        # Adjustments section
        self.adjustments_inputs = {}
        adj_box = QGroupBox("PALAWAN ADJUSTMENTS")
        adj_box.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid #F59E0B;
                border-radius: {_sz(6)}px;
                margin-top: {_sz(22)}px;
                padding: {_sz(14)}px {_sz(12)}px {_sz(12)}px {_sz(12)}px;
                background-color: #FFFBEB;
            }}
            QGroupBox::title {{
                color: #D97706;
                font-weight: 800;
                font-size: {_sz(12)}px;
                letter-spacing: 1px;
                padding: 1px {_sz(8)}px;
                background-color: #FFFBEB;
                border-radius: {_sz(4)}px;
            }}
        """)
        adj_form = QFormLayout()
        adj_form.setSpacing(_sz(8))
        adj_form.setContentsMargins(_sz(8), _sz(18), _sz(8), _sz(8))
        for adj_label, adj_placeholder in [
            ("Palawan Pay Out Incentives", "Enter Incentives Amount"),
            ("Palawan Suki Discounts",     "Enter Suki Discounts"),
            ("Palawan Suki Rebates",       "Enter Suki Rebates"),
            ("Palawan Cancel",             "Enter Cancellation Amount"),
        ]:
            inp = QLineEdit()
            inp.setValidator(QDoubleValidator(0.0, 1e12, 2))
            inp.setPlaceholderText(adj_placeholder)
            self.adjustments_inputs[adj_label] = inp
            lbl = QLabel(adj_label + ":")
            lbl.setStyleSheet(f"font-size: {_sz(13)}px; font-weight: 600; color: #92400E;")
            adj_form.addRow(lbl, inp)
        adj_box.setLayout(adj_form)
        inner_layout.addWidget(adj_box)

        # Save button row
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._save_btn = QPushButton("Save Palawan A")
        self._save_btn.setFixedHeight(_sz(36))
        self._save_btn.setMinimumWidth(_sz(200))
        self._save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_SAVE_COLOR};
                color: #FFFFFF;
                border: none;
                border-radius: {_sz(6)}px;
                font-size: {_sz(13)}px;
                font-weight: 700;
                padding: 0 {_sz(24)}px;
            }}
            QPushButton:hover   {{ background-color: {_SAVE_HOVER}; }}
            QPushButton:pressed {{ background-color: #000000; }}
        """)
        self._save_btn.clicked.connect(self._save)
        btn_row.addWidget(self._save_btn)
        inner_layout.addLayout(btn_row)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def _make_section(self, title: str, color: str):
        """Create one group box with Lotes + Principal + SC + Commission + TOTAL."""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {color};
                border-radius: {_sz(6)}px;
                margin-top: {_sz(22)}px;
                padding: {_sz(14)}px {_sz(12)}px {_sz(12)}px {_sz(12)}px;
                background-color: {_WHITE};
            }}
            QGroupBox::title {{
                color: {color};
                font-weight: 800;
                font-size: {_sz(12)}px;
                letter-spacing: 1px;
                padding: 1px {_sz(8)}px;
                background-color: {_WHITE};
                border-radius: {_sz(4)}px;
            }}
        """)
        form = QFormLayout()
        form.setSpacing(_sz(8))
        form.setContentsMargins(_sz(8), _sz(18), _sz(8), _sz(8))

        fields = {}

        # Lotes (integer)
        lotes_field = QLineEdit()
        lotes_field.setValidator(QIntValidator(0, 999999))
        lotes_field.setPlaceholderText("0")
        lbl = QLabel("Lotes:")
        lbl.setStyleSheet(f"font-size: {_sz(13)}px; font-weight: 600; color: {_SLATE_700};")
        form.addRow(lbl, lotes_field)
        fields["lotes"] = lotes_field

        # Principal / SC / Commission (decimal)
        for key, label_text in [("principal", "Principal:"), ("sc", "SC:"), ("commission", "Commission:")]:
            f = QLineEdit()
            f.setValidator(QDoubleValidator(0.0, 1e12, 2))
            f.setPlaceholderText("0.00")
            lbl2 = QLabel(label_text)
            lbl2.setStyleSheet(f"font-size: {_sz(13)}px; font-weight: 600; color: {_SLATE_700};")
            form.addRow(lbl2, f)
            fields[key] = f

        # TOTAL (read-only display)
        total_display = QLineEdit("0.00")
        total_display.setReadOnly(True)
        total_display.setStyleSheet(
            f"font-weight: 800; font-size: {_sz(13)}px; color: {color}; "
            f"background-color: {_SLATE_50}; border: 1px solid {_SLATE_200}; "
            f"border-radius: {_sz(4)}px; padding: {_sz(6)}px {_sz(10)}px;"
        )
        total_lbl = QLabel("TOTAL:")
        total_lbl.setStyleSheet(f"font-weight: 700; color: {color}; font-size: {_sz(13)}px;")
        form.addRow(total_lbl, total_display)
        fields["total_display"] = total_display

        # Wire up recalc signals
        for key in ("principal", "sc", "commission"):
            fields[key].textChanged.connect(
                lambda _text, flds=fields, td=total_display: self._recalc_section(flds, td)
            )
        lotes_field.textChanged.connect(
            lambda _text, flds=fields, td=total_display: self._recalc_section(flds, td)
        )

        group.setLayout(form)
        return group, fields

    def _recalc_section(self, fields: dict, total_display: QLineEdit):
        total = 0.0
        for key in ("principal", "sc", "commission"):
            try:
                total += float(fields[key].text().strip() or 0)
            except ValueError:
                pass
        total_display.setText(f"{total:.2f}")

    # ──────────────────────────────────────────────────────────────────────
    # DATA ACCESS
    # ──────────────────────────────────────────────────────────────────────
    def get_data(self) -> dict:
        """Return current field values as a dict for DB insertion."""
        def _int(f):
            try: return int(f.text().strip() or 0)
            except ValueError: return 0
        def _dec(f):
            try: return float(f.text().strip() or 0)
            except ValueError: return 0.0

        sf, pf, inf = self._so_fields, self._po_fields, self._int_fields
        adj = self.adjustments_inputs
        return {
            "so_lotes":       _int(sf["lotes"]),
            "so_principal":   _dec(sf["principal"]),
            "so_sc":          _dec(sf["sc"]),
            "so_commission":  _dec(sf["commission"]),
            "so_total":       _dec(sf["total_display"]),
            "po_lotes":       _int(pf["lotes"]),
            "po_principal":   _dec(pf["principal"]),
            "po_sc":          _dec(pf["sc"]),
            "po_commission":  _dec(pf["commission"]),
            "po_total":       _dec(pf["total_display"]),
            "int_lotes":      _int(inf["lotes"]),
            "int_principal":  _dec(inf["principal"]),
            "int_sc":         _dec(inf["sc"]),
            "int_commission": _dec(inf["commission"]),
            "int_total":      _dec(inf["total_display"]),
            "palawan_pay_out_incentives": _dec(adj.get("Palawan Pay Out Incentives", QLineEdit())),
            "palawan_suki_discounts":     _dec(adj.get("Palawan Suki Discounts",     QLineEdit())),
            "palawan_suki_rebates":       _dec(adj.get("Palawan Suki Rebates",       QLineEdit())),
            "palawan_cancel":             _dec(adj.get("Palawan Cancel",             QLineEdit())),
        }

    def load_data(self, data: dict):
        """Populate fields from a DB row dict (so_*/po_*/int_* keys)."""
        def _set_int(f, val):
            f.blockSignals(True)
            f.setText(str(int(val or 0)) if (val or 0) else "")
            f.blockSignals(False)

        def _set_dec(f, val):
            f.blockSignals(True)
            v = float(val or 0)
            f.setText(f"{v:.2f}" if v else "")
            f.blockSignals(False)

        for prefix, fields in [("so", self._so_fields), ("po", self._po_fields), ("int", self._int_fields)]:
            _set_int(fields["lotes"],      data.get(f"{prefix}_lotes", 0))
            _set_dec(fields["principal"],  data.get(f"{prefix}_principal", 0))
            _set_dec(fields["sc"],         data.get(f"{prefix}_sc", 0))
            _set_dec(fields["commission"], data.get(f"{prefix}_commission", 0))
            self._recalc_section(fields, fields["total_display"])
        adj_map = {
            "Palawan Pay Out Incentives": "palawan_pay_out_incentives",
            "Palawan Suki Discounts":     "palawan_suki_discounts",
            "Palawan Suki Rebates":       "palawan_suki_rebates",
            "Palawan Cancel":             "palawan_cancel",
        }
        for label, db_key in adj_map.items():
            if label in self.adjustments_inputs:
                _set_dec(self.adjustments_inputs[label], data.get(db_key, 0))

    def clear_fields(self):
        for fields in (self._so_fields, self._po_fields, self._int_fields):
            for key in ("lotes", "principal", "sc", "commission"):
                fields[key].blockSignals(True)
                fields[key].clear()
                fields[key].blockSignals(False)
            fields["total_display"].setText("0.00")
        for inp in self.adjustments_inputs.values():
            inp.blockSignals(True)
            inp.clear()
            inp.blockSignals(False)

    def set_enabled(self, enabled: bool):
        for fields in (self._so_fields, self._po_fields, self._int_fields):
            for key in ("lotes", "principal", "sc", "commission"):
                fields[key].setEnabled(enabled)
        for inp in self.adjustments_inputs.values():
            inp.setEnabled(enabled)
        self._save_btn.setEnabled(enabled)

    # ──────────────────────────────────────────────────────────────────────
    # SAVE (standalone)
    # ──────────────────────────────────────────────────────────────────────
    def _save(self):
        dash = self._dashboard
        sd = dash.date_picker.date().toString("yyyy-MM-dd")
        data = self.get_data()
        try:
            dash.db_manager.execute_query(
                """INSERT INTO payable_tbl_brand_a
                   (corporation, branch, date,
                    sendout_lotes, sendout_capital, sendout_sc, sendout_commission, sendout_total,
                    payout_lotes,  payout_capital,  payout_sc,  payout_commission,  payout_total,
                    international_lotes, international_capital, international_sc,
                    international_commission, international_total)
                   VALUES (%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s)
                   ON DUPLICATE KEY UPDATE
                    sendout_lotes=VALUES(sendout_lotes),
                    sendout_capital=VALUES(sendout_capital),
                    sendout_sc=VALUES(sendout_sc),
                    sendout_commission=VALUES(sendout_commission),
                    sendout_total=VALUES(sendout_total),
                    payout_lotes=VALUES(payout_lotes),
                    payout_capital=VALUES(payout_capital),
                    payout_sc=VALUES(payout_sc),
                    payout_commission=VALUES(payout_commission),
                    payout_total=VALUES(payout_total),
                    international_lotes=VALUES(international_lotes),
                    international_capital=VALUES(international_capital),
                    international_sc=VALUES(international_sc),
                    international_commission=VALUES(international_commission),
                    international_total=VALUES(international_total),
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    dash.corporation, dash.branch, sd,
                    data["so_lotes"],  data["so_principal"],  data["so_sc"],
                    data["so_commission"],  data["so_total"],
                    data["po_lotes"],  data["po_principal"],  data["po_sc"],
                    data["po_commission"],  data["po_total"],
                    data["int_lotes"], data["int_principal"], data["int_sc"],
                    data["int_commission"], data["int_total"],
                )
            )
            QMessageBox.information(self, "Saved", f"Palawan Payable A saved for {sd}.")
            logger.info("[PalawanPayableTab] saved for branch=%s date=%s", dash.branch, sd)
        except Exception as e:
            logger.error("[PalawanPayableTab] save error: %s", e)
            QMessageBox.critical(self, "Error", f"Failed to save Palawan Payable A:\n{e}")
