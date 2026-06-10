"""
PalawanDetailsTab
-----------------
Tab widget for Palawan Details (Brand B) data entry.
Design matches PalawanPayableTab.

Provides data-entry for:
  - PALAWAN SEND-OUT      : Lotes, Principal, SC, Commission, TOTAL
  - PALAWAN PAY-OUT       : Lotes, Principal, SC, Commission, TOTAL
  - PALAWAN INTERNATIONAL : Lotes, Principal, SC, Commission, TOTAL
  - PALAWAN ADJUSTMENTS

Data is saved to `payable_tbl_brand_a` (shared with Brand A).
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QPushButton, QScrollArea, QFrame,
    QMessageBox,
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


class PalawanDetailsTab(QWidget):
    """Tab widget for Palawan Details (Brand B) - design matches PalawanPayableTab."""

    def set_enabled(self, enabled: bool):
        """Enable or disable all input fields."""
        for fields in (self._so_fields, self._po_fields, self._int_fields):
            for key in ("lotes", "principal", "sc", "commission"):
                fields[key].setEnabled(enabled)
        for inp in self.adjustments_inputs.values():
            inp.setEnabled(enabled)
        if hasattr(self, '_save_btn'):
            self._save_btn.setEnabled(enabled)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._dashboard = parent  # alias used by _save()
        self._setup_ui()

    # ──────────────────────────────────────────────────────────────────────
    # UI BUILD
    # ──────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(_sz(12), _sz(12), _sz(12), _sz(12))
        outer.setSpacing(_sz(10))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        inner = QWidget()
        inner.setStyleSheet(f"background-color: {_WHITE};")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(_sz(12), _sz(10), _sz(12), _sz(10))
        inner_layout.setSpacing(_sz(10))

        title = QLabel("PALAWAN DETAILS — BRAND B")
        title.setStyleSheet(
            f"color: {_SLATE_800}; font-size: {_sz(14)}px; font-weight: 800; "
            f"letter-spacing: 1.5px; background: transparent;"
        )
        inner_layout.addWidget(title)

        # Three section groups side by side
        sections_row = QHBoxLayout()
        sections_row.setSpacing(_sz(10))

        self._so_group,  self._so_fields  = self._make_section("PALAWAN SEND-OUT",     _SO_COLOR)
        self._po_group,  self._po_fields  = self._make_section("PALAWAN PAY-OUT",       _PO_COLOR)
        self._int_group, self._int_fields = self._make_section("PALAWAN INTERNATIONAL", _INT_COLOR)

        sections_row.addWidget(self._so_group)
        sections_row.addWidget(self._po_group)
        sections_row.addWidget(self._int_group)
        inner_layout.addLayout(sections_row)

        # Adjustments section
        self.adjustments_inputs = {}
        adj_box = QGroupBox("PALAWAN ADJUSTMENTS (Auto-carries to Brand B Cash Flow)")
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

        for adj_label, adj_placeholder, db_col in [
            ("Palawan Pay Out Incentives", "Enter Incentives Amount",   "palawan_pay_out_incentives"),
            ("Palawan Suki Discounts",     "Enter Suki Discounts",      "palawan_suki_discounts"),
            ("Palawan Suki Rebates",       "Enter Suki Rebates",        "palawan_suki_rebates"),
            ("Palawan Cancel",             "Enter Cancellation Amount", "palawan_cancel"),
        ]:
            inp = QLineEdit()
            inp.setValidator(QDoubleValidator(0.0, 1e12, 2))
            inp.setPlaceholderText(adj_placeholder)
            inp.setProperty("db_column", db_col)
            inp.textChanged.connect(self.parent.recalculate_all)
            self.adjustments_inputs[adj_label] = inp
            lbl = QLabel(adj_label + ":")
            lbl.setStyleSheet(f"font-size: {_sz(13)}px; font-weight: 600; color: #92400E;")
            adj_form.addRow(lbl, inp)

        adj_box.setLayout(adj_form)
        inner_layout.addWidget(adj_box)

        # Note: Palawan data is now saved with main report posting via post_button
        inner_layout.addStretch()
        scroll.setWidget(inner)
        outer.addWidget(scroll)

        # ── Legacy aliases used by _connect_palawan_adjustments_to_brand_b ──
        self.sendout_inputs = {
            "Principal":  self._so_fields["principal"],
            "SC":         self._so_fields["sc"],
            "Commission": self._so_fields["commission"],
        }
        self.payout_inputs = {
            "Principal":  self._po_fields["principal"],
            "SC":         self._po_fields["sc"],
            "Commission": self._po_fields["commission"],
        }
        self.international_inputs = {
            "Principal":  self._int_fields["principal"],
            "SC":         self._int_fields["sc"],
            "Commission": self._int_fields["commission"],
        }
        self.lotes_inputs = {
            "Lotes Send-Out":      self._so_fields["lotes"],
            "Lotes Pay-Out":       self._po_fields["lotes"],
            "Lotes International": self._int_fields["lotes"],
        }
        self.sendout_total_display       = self._so_fields["total_display"]
        self.payout_total_display        = self._po_fields["total_display"]
        self.international_total_display = self._int_fields["total_display"]

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

    # ── Compat shims used by old code ──────────────────────────────────────
    def calculate_palawan_totals(self):
        for flds in (self._so_fields, self._po_fields, self._int_fields):
            self._recalc_section(flds, flds["total_display"])

    def calculate_lotes_total(self):
        pass  # lotes totals are per-section now

    def calculate_adjustments_total(self):
        pass  # no separate adjustments total display

    def create_money_input(self, placeholder=""):
        field = QLineEdit()
        field.setValidator(QDoubleValidator(0.0, 1e12, 2))
        field.setPlaceholderText(placeholder)
        field.textChanged.connect(self.parent.recalculate_all)
        return field

    # ──────────────────────────────────────────────────────────────────────
    # DATA ACCESS
    # ──────────────────────────────────────────────────────────────────────
    def get_data(self) -> dict:
        """Return current field values as a dict for DB insertion.
        Returns same keys as PalawanPayableTab so _save_palawan_to_payable
        can use a single code path for both brands."""
        def _int(f):
            try: return int(float(f.text().strip() or 0))
            except ValueError: return 0

        def _dec(f):
            try: return float(f.text().strip() or 0)
            except ValueError: return 0.0

        sf, pf, inf = self._so_fields, self._po_fields, self._int_fields
        adj = self.adjustments_inputs

        result = {
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

        # Legacy aliases so _restore_palawan_tab / cashflow mirror still work
        result["palawan_sendout_principal"]           = result["so_principal"]
        result["palawan_sendout_sc"]                  = result["so_sc"]
        result["palawan_sendout_commission"]          = result["so_commission"]
        result["palawan_sendout_regular_total"]       = result["so_total"]
        result["palawan_sendout_lotes_total"]         = result["so_lotes"]
        result["palawan_payout_principal"]            = result["po_principal"]
        result["palawan_payout_sc"]                   = result["po_sc"]
        result["palawan_payout_commission"]           = result["po_commission"]
        result["palawan_payout_regular_total"]        = result["po_total"]
        result["palawan_payout_lotes_total"]          = result["po_lotes"]
        result["palawan_international_principal"]     = result["int_principal"]
        result["palawan_international_sc"]            = result["int_sc"]
        result["palawan_international_commission"]    = result["int_commission"]
        result["palawan_international_regular_total"] = result["int_total"]
        result["palawan_international_lotes_total"]   = result["int_lotes"]

        # Debug: Log adjustment values being collected from UI
        import logging
        logger = logging.getLogger(__name__)
        adj_inc = result.get("palawan_pay_out_incentives", 0)
        adj_skid = result.get("palawan_suki_discounts", 0)
        adj_skir = result.get("palawan_suki_rebates", 0)
        adj_cancel = result.get("palawan_cancel", 0)
        if adj_inc or adj_skid or adj_skir or adj_cancel:
            logger.info(f"🔵 PalawanDetailsTab.get_data() adjustments: inc={adj_inc}, skid={adj_skid}, skir={adj_skir}, cancel={adj_cancel}")
        else:
            logger.debug(f"PalawanDetailsTab.get_data() - no adjustments entered")

        return result

    def load_data(self, data: dict):
        """Populate all tab fields from a DB row dict.
        Accepts new-format keys (so_*/po_*/int_*) from payable_tbl_brand_a
        or old-format keys (palawan_sendout_*) from daily_reports tables."""
        def _set_int(f, val):
            f.blockSignals(True)
            try:
                n = int(float(val or 0))
            except (TypeError, ValueError):
                n = 0
            f.setText(str(n) if n else "")
            f.blockSignals(False)

        def _set_dec(f, val):
            f.blockSignals(True)
            v = float(val or 0)
            f.setText(f"{v:.2f}" if v else "")
            f.blockSignals(False)

        def _get(new_key, old_key):
            """Prefer new-format key; fall back to old palawan_* key."""
            v = data.get(new_key)
            if v is None or (isinstance(v, (int, float)) and v == 0):
                v = data.get(old_key, 0)
            return v

        for prefix, fields, old_pfx in [
            ("so",  self._so_fields,  "palawan_sendout"),
            ("po",  self._po_fields,  "palawan_payout"),
            ("int", self._int_fields, "palawan_international"),
        ]:
            _set_int(fields["lotes"],      _get(f"{prefix}_lotes",      f"{old_pfx}_lotes_total"))
            _set_dec(fields["principal"],  _get(f"{prefix}_principal",  f"{old_pfx}_principal"))
            _set_dec(fields["sc"],         _get(f"{prefix}_sc",         f"{old_pfx}_sc"))
            _set_dec(fields["commission"], _get(f"{prefix}_commission",  f"{old_pfx}_commission"))
            self._recalc_section(fields, fields["total_display"])

        adj_map = {
            "Palawan Pay Out Incentives": "palawan_pay_out_incentives",
            "Palawan Suki Discounts":     "palawan_suki_discounts",
            "Palawan Suki Rebates":       "palawan_suki_rebates",
            "Palawan Cancel":             "palawan_cancel",
        }
        print(f"🔵 DEBUG load_data: adjustments_inputs keys: {list(self.adjustments_inputs.keys())}")
        print(f"🔵 DEBUG load_data: data dict keys: {list(data.keys())}")
        for label, db_key in adj_map.items():
            val = data.get(db_key, 0)
            in_dict = label in self.adjustments_inputs
            print(f"🔵 DEBUG load_data: label='{label}', in_dict={in_dict}, db_key='{db_key}', value={val}")
            if label in self.adjustments_inputs:
                print(f"   ✅ Setting {label} = {val}")
                _set_dec(self.adjustments_inputs[label], val)
            else:
                print(f"   ❌ {label} NOT found in adjustments_inputs!")

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

    # ──────────────────────────────────────────────────────────────────────
    # STANDALONE SAVE
    # ──────────────────────────────────────────────────────────────────────
    def _save(self):
        """Save button handler — writes to payable_tbl_brand_a."""
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
            QMessageBox.information(self, "Saved", f"Palawan Details B saved for {sd}.")
            logger.info("[PalawanDetailsTab] saved for branch=%s date=%s", dash.branch, sd)
        except Exception as e:
            logger.error("[PalawanDetailsTab] save error: %s", e)
            QMessageBox.critical(self, "Error", f"Failed to save Palawan Details B:\n{e}")