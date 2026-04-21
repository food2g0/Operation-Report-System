import json
import os
import re

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QScrollArea, QFrame, QPushButton,
    QDialog, QComboBox, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtCore import Qt

from Client.ui_scaling import _sz


try:
    from db_connect_pooled import db_manager
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False


import sys as _sys

def _get_config_dir() -> str:

    if getattr(_sys, 'frozen', False):

        return os.path.dirname(_sys.executable)
 
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_BASE_DIR = _get_config_dir()
FIELD_CONFIG_PATH = os.path.join(_BASE_DIR, "field_config.json")


_field_config_cache = None
_field_config_cache_time = 0
_CACHE_TTL = 300 


def _load_field_config_from_db() -> dict:
    
    if not _DB_AVAILABLE:
        return None
    try:
        result = db_manager.execute_query(
            "SELECT config_value FROM field_config WHERE config_key = 'field_definitions'"
        )
        if result and result[0].get('config_value'):
            return json.loads(result[0]['config_value'])
    except Exception as exc:
        print(f"[CashFlowTab] Failed to load config from DB: {exc}")
    return None


def _load_field_config() -> dict:

    global _field_config_cache, _field_config_cache_time
    import time
    

    current_time = time.time()
    if _field_config_cache and (current_time - _field_config_cache_time) < _CACHE_TTL:
        return _field_config_cache
    

    db_cfg = _load_field_config_from_db()
    if db_cfg:

        for brand in ("Brand A", "Brand B"):
            db_cfg.setdefault(brand, {})
            db_cfg[brand].setdefault("debit", [])
            db_cfg[brand].setdefault("credit", [])
        _field_config_cache = db_cfg
        _field_config_cache_time = current_time
        return db_cfg
    

    try:
        with open(FIELD_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        _field_config_cache = cfg
        _field_config_cache_time = current_time
        return cfg
    except Exception:
        return {"Brand A": {"debit": [], "credit": []},
                "Brand B": {"debit": [], "credit": []}}


def refresh_field_config_cache():

    global _field_config_cache, _field_config_cache_time
    _field_config_cache = None
    _field_config_cache_time = 0


def _sanitize_column(name: str) -> str:
    col = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return col


class MCCurrencyDialog(QDialog):

    
    CURRENCIES = [
        "USD - US Dollar",
        "EUR - Euro",
        "JPY - Japanese Yen",
        "KRW - Korean Won",
        "CNY - Chinese Yuan",
        "SGD - Singapore Dollar",
        "AED - UAE Dirham",
        "SAR - Saudi Riyal",
        "AUD - Australian Dollar",
        "CAD - Canadian Dollar",
        "GBP - British Pound",
        "HKD - Hong Kong Dollar",
        "CHF - Swiss Franc",
        "NOK - Norwegian Krone",
        "SEK - Swedish Krona",
        "THB - Thai Baht",
        "MYR - Malaysian Ringgit",
        "IDR - Indonesian Rupiah",
        "VND - Vietnamese Dong",
        "TWD - Taiwan Dollar"
    ]
    
    def __init__(self, parent, field_type, existing_entries=None):
        super().__init__(parent)
        self.field_type = field_type 
        self.entries = existing_entries or []
        self.entry_widgets = []
        
        self.setWindowTitle(f"{field_type} - {'Selling' if field_type == 'MC In' else 'Buying'} Currency")
        self.setMinimumWidth(750)
        self.setMinimumHeight(400)
        
        self.setup_ui()
        self.load_existing_entries()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
   
        header_text = "SELLING Currency (Money Coming In)" if self.field_type == "MC In" else "BUYING Currency (Money Going Out)"
        header_color = "#22C55E" if self.field_type == "MC In" else "#DC2626"
        
        header = QLabel(f"💱 {header_text}")
        header.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {header_color}; padding: 10px;")
        layout.addWidget(header)
        

        instructions = QLabel(
            "Enter currency details: Pcs × Denomination × Rate = Total PHP\n"
            "Example: 2 pcs × 100 USD × 58.00 = ₱11,600.00"
        )
        instructions.setStyleSheet("font-size: 13px; color: #64748B; padding: 5px;")
        layout.addWidget(instructions)
        

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(200)
        
        self.entries_widget = QWidget()
        self.entries_layout = QVBoxLayout(self.entries_widget)
        scroll.setWidget(self.entries_widget)
        layout.addWidget(scroll)
        
    
        if not self.entries:
            self.add_entry()
        

        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add Entry")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #22C55E;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #16A34A; }
        """)
        add_btn.clicked.connect(self.add_entry)
        
        remove_btn = QPushButton("➖ Remove Last")
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #EF4444;
                border: 2px solid #EF4444;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #FEF2F2; }
        """)
        remove_btn.clicked.connect(self.remove_entry)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Total display
        total_frame = QFrame()
        total_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {'#F0FDF4' if self.field_type == 'MC In' else '#FEF2F2'};
                border: 1px solid {'#BBF7D0' if self.field_type == 'MC In' else '#FECACA'};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        total_layout = QHBoxLayout(total_frame)
        
        total_label = QLabel("TOTAL PHP:")
        total_label.setStyleSheet(f"font-weight: 700; color: {header_color};")
        self.total_display = QLabel("₱0.00")
        self.total_display.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {header_color};")
        
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_display)
        total_layout.addStretch()
        layout.addWidget(total_frame)
        

        dialog_btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #475569;
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        ok_btn = QPushButton("Apply")
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {header_color};
                color: white;
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        ok_btn.clicked.connect(self.accept)
        
        dialog_btn_layout.addStretch()
        dialog_btn_layout.addWidget(cancel_btn)
        dialog_btn_layout.addWidget(ok_btn)
        layout.addLayout(dialog_btn_layout)
    
    def add_entry(self, currency_idx=0, quantity="", denomination="", rate=""):
        entry_frame = QFrame()
        entry_frame.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 8px;
                margin: 2px 0;
            }
        """)
        
        entry_layout = QHBoxLayout(entry_frame)
        

        entry_num = len(self.entry_widgets) + 1
        num_label = QLabel(f"#{entry_num}")
        num_label.setStyleSheet("font-weight: 700; color: #3B82F6; min-width: 30px;")
        entry_layout.addWidget(num_label)
        
   
        currency_combo = QComboBox()
        currency_combo.addItems(self.CURRENCIES)
        currency_combo.setCurrentIndex(currency_idx)
        currency_combo.setMaxVisibleItems(20)
        currency_combo.setStyleSheet("min-width: 160px; padding: 5px;")
        entry_layout.addWidget(QLabel("Currency:"))
        entry_layout.addWidget(currency_combo)
        

        qty_input = QLineEdit()
        qty_input.setValidator(QIntValidator(0, 999999))
        qty_input.setPlaceholderText("Pcs")
        qty_input.setText(quantity)
        qty_input.setStyleSheet("min-width: 50px; padding: 5px;")
        qty_input.textChanged.connect(self.calculate_total)
        entry_layout.addWidget(QLabel("Pcs:"))
        entry_layout.addWidget(qty_input)
        
  
        denom_input = QLineEdit()
        denom_input.setValidator(QDoubleValidator(0.0, 999999.99, 2))
        denom_input.setPlaceholderText("Denom")
        denom_input.setText(denomination)
        denom_input.setStyleSheet("min-width: 60px; padding: 5px;")
        denom_input.textChanged.connect(self.calculate_total)
        entry_layout.addWidget(QLabel("Denom:"))
        entry_layout.addWidget(denom_input)
        

        rate_input = QLineEdit()
        rate_input.setValidator(QDoubleValidator(0.0, 999999.99, 2))
        rate_input.setPlaceholderText("Rate")
        rate_input.setText(rate)
        rate_input.setStyleSheet("min-width: 60px; padding: 5px;")
        rate_input.textChanged.connect(self.calculate_total)
        entry_layout.addWidget(QLabel("Rate:"))
        entry_layout.addWidget(rate_input)
        

        subtotal_label = QLabel("₱0.00")
        subtotal_label.setStyleSheet("font-weight: 700; min-width: 100px;")
        entry_layout.addWidget(QLabel("Total:"))
        entry_layout.addWidget(subtotal_label)
        
        self.entries_layout.addWidget(entry_frame)
        self.entry_widgets.append({
            'frame': entry_frame,
            'num_label': num_label,
            'currency_combo': currency_combo,
            'qty_input': qty_input,
            'denom_input': denom_input,
            'rate_input': rate_input,
            'subtotal_label': subtotal_label
        })
        
        self.calculate_total()
    
    def remove_entry(self):
        if len(self.entry_widgets) > 1:
            entry = self.entry_widgets.pop()
            entry['frame'].setParent(None)
            entry['frame'].deleteLater()
            self.renumber_entries()
            self.calculate_total()
    
    def renumber_entries(self):
        for i, entry in enumerate(self.entry_widgets):
            entry['num_label'].setText(f"#{i + 1}")
    
    def calculate_total(self):
        total = 0.0
        for entry in self.entry_widgets:
            try:
                qty = int(entry['qty_input'].text().strip()) if entry['qty_input'].text().strip() else 0
                denom = float(entry['denom_input'].text().strip()) if entry['denom_input'].text().strip() else 0.0
                rate = float(entry['rate_input'].text().strip()) if entry['rate_input'].text().strip() else 0.0

                subtotal = qty * denom * rate
                entry['subtotal_label'].setText(f"₱{subtotal:,.2f}")
                total += subtotal
            except (ValueError, AttributeError):
                entry['subtotal_label'].setText("₱0.00")
        
        if hasattr(self, 'total_display'):
            self.total_display.setText(f"₱{total:,.2f}")
        return total
    
    def load_existing_entries(self):
        for entry_data in self.entries:
            self.add_entry(
                currency_idx=entry_data.get('currency_index', 0),
                quantity=str(entry_data.get('quantity', '')),
                denomination=str(entry_data.get('denomination', '')),
                rate=str(entry_data.get('rate', ''))
            )
    
    def get_entries(self):
       
        entries = []
        for entry in self.entry_widgets:
            qty_text = entry['qty_input'].text().strip()
            denom_text = entry['denom_input'].text().strip()
            rate_text = entry['rate_input'].text().strip()
            qty = int(qty_text) if qty_text else 0
            denom = float(denom_text) if denom_text else 0.0
            rate = float(rate_text) if rate_text else 0.0
            total_php = qty * denom * rate
            entries.append({
                'currency_index': entry['currency_combo'].currentIndex(),
                'currency': entry['currency_combo'].currentText(),
                'quantity': qty,
                'denomination': denom,
                'rate': rate,
                'total_php': total_php
            })
        return entries
    
    def get_total(self):
        return self.calculate_total()


class CashFlowTab(QWidget):
    def __init__(self, parent, brand_name="Brand A"):
        super().__init__()
        self.parent = parent
        self.brand_name = brand_name 

        self.debit_inputs = {}
        self.credit_inputs = {}
        self.debit_lotes_inputs = {}
        self.credit_lotes_inputs = {}
        
        self.branch_dest_inputs = {}
        
        self.mc_currency_details = {
            'MC In': [],
            'MC Out': []
        }
        

        self.selected_bank_account = None
        self.bank_account_btn = None


        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(_sz(10))

        self.setup_ui()

    def setup_ui(self):
        """Setup UI based on current brand"""
        brand_color = "#3B82F6" if self.brand_name == "Brand A" else "#8B5CF6"
        brand_color_light = "#EFF6FF" if self.brand_name == "Brand A" else "#F5F3FF"


        debit_scroll = QScrollArea()
        debit_scroll.setWidgetResizable(True)

        debit_box = QGroupBox("")
        debit_box.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid #E2E8F0;
                border-radius: {_sz(6)}px;
                margin-top: {_sz(22)}px;
                padding: {_sz(18)}px {_sz(16)}px {_sz(16)}px {_sz(16)}px;
            }}
            QGroupBox::title {{
                color: #EF4444;
                font-size: {_sz(13)}px;
                font-weight: 800;
                letter-spacing: 1.2px;
                padding: 1px {_sz(8)}px;
                background-color: #FFFFFF;
                border-radius: {_sz(4)}px;
            }}
        """)
        debit_form = QFormLayout()
        debit_form.setSpacing(_sz(10))
        debit_form.setContentsMargins(_sz(16), _sz(24), _sz(16), _sz(16))

        debit_fields = self.get_debit_fields()
        self.debit_inputs = self.build_input_group(debit_form, debit_fields, is_debit=True)

        debit_form.addRow(self.parent.create_separator(), QLabel(""))
        self.debit_total_display = self.parent.create_display_field("0.00")
        self.debit_total_display.setStyleSheet(
            f"font-weight: 800; font-size: {_sz(15)}px; color: #059669; "
            f"background-color: #F0FDF4; border: 1px solid #BBF7D0; "
            f"border-radius: {_sz(6)}px; padding: {_sz(7)}px {_sz(14)}px;"
        )
        total_label = QLabel("Total Cash Receipt:")
        total_label.setStyleSheet(f"font-weight: 700; color: #059669; font-size: {_sz(14)}px;")
        debit_form.addRow(total_label, self.debit_total_display)

        debit_box.setLayout(debit_form)
        debit_scroll.setWidget(debit_box)

   
        credit_scroll = QScrollArea()
        credit_scroll.setWidgetResizable(True)

        credit_box = QGroupBox("")
        credit_box.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid #E2E8F0;
                border-radius: {_sz(6)}px;
                margin-top: {_sz(22)}px;
                padding: {_sz(18)}px {_sz(16)}px {_sz(16)}px {_sz(16)}px;
            }}
            QGroupBox::title {{
                color: #16A34A;
                font-size: {_sz(13)}px;
                font-weight: 800;
                letter-spacing: 1.2px;
                padding: 1px {_sz(8)}px;
                background-color: #FFFFFF;
                border-radius: {_sz(4)}px;
            }}
        """)
        credit_form = QFormLayout()
        credit_form.setSpacing(_sz(10))
        credit_form.setContentsMargins(_sz(16), _sz(24), _sz(16), _sz(16))

        credit_fields = self.get_credit_fields()
        self.credit_inputs = self.build_input_group(credit_form, credit_fields, is_debit=False)

        credit_form.addRow(self.parent.create_separator(), QLabel(""))
        self.credit_total_display = self.parent.create_display_field("0.00")
        self.credit_total_display.setStyleSheet(
            f"font-weight: 800; font-size: {_sz(15)}px; color: #EF4444; "
            f"background-color: #FEF2F2; border: 1px solid #FECACA; "
            f"border-radius: {_sz(6)}px; padding: {_sz(7)}px {_sz(14)}px;"
        )
        total_label = QLabel("Total Cash Out:")
        total_label.setStyleSheet(f"font-weight: 700; color: #EF4444; font-size: {_sz(14)}px;")
        credit_form.addRow(total_label, self.credit_total_display)

        credit_box.setLayout(credit_form)
        credit_scroll.setWidget(credit_box)

        self.main_layout.addWidget(debit_scroll)
        self.main_layout.addWidget(credit_scroll)

    def get_debit_fields(self):
      
        cfg = _load_field_config()
        entries = cfg.get(self.brand_name, {}).get("debit", [])
        if entries:
            return [(e[0], e[1] if len(e) >= 2 else f"Enter {e[0]}") for e in entries]
        
        return []

    def get_credit_fields(self):
   
        cfg = _load_field_config()
        entries = cfg.get(self.brand_name, {}).get("credit", [])
        if entries:
            return [(e[0], e[1] if len(e) >= 2 else f"Enter {e[0]}") for e in entries]
        return []

    def build_input_group(self, form_layout, fields, is_debit=True):
   
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

            if label_text in ("MC In", "MC Out"):
                if self.brand_name == "Brand A":
                    amount_field.setReadOnly(True)
                amount_field.setStyleSheet(
                    f"background-color: #F1F5F9; border: 1px solid #CBD5E1; "
                    f"border-radius: {_sz(5)}px; padding: {_sz(5)}px {_sz(10)}px; font-size: {_sz(14)}px; "
                    f"color: #475569; font-weight: 600; min-height: {_sz(34)}px;"
                )
                mc_btn = QPushButton("💱")
                mc_btn.setFixedSize(_sz(34), _sz(34))
                mc_btn.setCursor(Qt.PointingHandCursor)
                mc_btn.setStyleSheet(
                    f"QPushButton {{ background-color: #3B82F6; color: white; "
                    f"border-radius: {_sz(6)}px; font-size: {_sz(16)}px; font-weight: bold; }} "
                    f"QPushButton:hover {{ background-color: #2563EB; }}"
                )
                mc_btn.setToolTip(f"Add {label_text} currency details")
                mc_btn.clicked.connect(lambda checked, lt=label_text, af=amount_field: self.open_mc_dialog(lt, af))
                row_layout.addWidget(mc_btn, 0)
                
                lotes_lbl = QLabel("Lotes:")
                lotes_lbl.setStyleSheet(f"font-size: {_sz(13)}px; font-weight: 600; color: #475569;")
                row_layout.addWidget(lotes_lbl, 0)
                row_layout.addWidget(lotes_field, 0)

            elif label_text == "Fund Transfer to HEAD OFFICE":
                bank_btn = QPushButton("Select Bank")
                bank_btn.setStyleSheet(
                    f"QPushButton {{ background-color: #8B5CF6; color: white; "
                    f"border: none; border-radius: {_sz(5)}px; font-size: {_sz(12)}px; "
                    f"font-weight: 700; padding: {_sz(6)}px {_sz(12)}px; }} "
                    f"QPushButton:hover {{ background-color: #7C3AED; }}"
                )
                bank_btn.setToolTip("Select bank account for fund transfer")
                bank_btn.clicked.connect(self.show_bank_account_selector)
                self.bank_account_btn = bank_btn
                row_layout.addWidget(bank_btn, 0)
   
            elif label_text == "Fund Transfer to BRANCH":
                branch_lbl = QLabel("To Branch:")
                branch_lbl.setStyleSheet(f"font-size: {_sz(13)}px; font-weight: 600; color: #475569;")
                row_layout.addWidget(branch_lbl, 0)
                
                branch_input = QLineEdit()
                branch_input.setPlaceholderText("Enter branch name")
                branch_input.setMaximumWidth(_sz(160))
                branch_input.setStyleSheet(
                    f"background-color: #F8FAFC; border: 1px solid #E2E8F0; "
                    f"border-radius: {_sz(5)}px; padding: {_sz(5)}px {_sz(10)}px; font-size: {_sz(14)}px; "
                    f"color: #1E293B; font-weight: 600; min-height: {_sz(34)}px;"
                )
                row_layout.addWidget(branch_input, 0)
                self.branch_dest_inputs[label_text] = branch_input

            elif label_text == "Fund Transfer from BRANCH":
                branch_lbl = QLabel("From:")
                branch_lbl.setStyleSheet(f"font-size: {_sz(12)}px; font-weight: 600; color: #475569;")
                row_layout.addWidget(branch_lbl, 0)
                
                branch_input = QLineEdit()
                branch_input.setPlaceholderText("Enter branch name")
                branch_input.setMaximumWidth(_sz(160))
                branch_input.setStyleSheet(
                    f"background-color: #F8FAFC; border: 1px solid #E2E8F0; "
                    f"border-radius: {_sz(5)}px; padding: {_sz(5)}px {_sz(10)}px; font-size: {_sz(14)}px; "
                    f"color: #1E293B; font-weight: 600; min-height: {_sz(34)}px;"
                )
                row_layout.addWidget(branch_input, 0)
                self.branch_dest_inputs[label_text] = branch_input
            else:
                lotes_lbl = QLabel("Lotes:")
                lotes_lbl.setStyleSheet(f"font-size: {_sz(13)}px; font-weight: 600; color: #475569;")
                row_layout.addWidget(lotes_lbl, 0)
                row_layout.addWidget(lotes_field, 0)

            label = QLabel(("Fund Transfer" if label_text == "Fund Transfer from BRANCH" else label_text) + ":")
            label.setStyleSheet(f"font-size: {_sz(14)}px; font-weight: 600; color: #1E293B;")
            form_layout.addRow(label, container)

            inputs[label_text] = amount_field
            lotes_inputs[label_text] = lotes_field

        return inputs

    def open_mc_dialog(self, field_type, amount_field):

        existing_entries = self.mc_currency_details.get(field_type, [])
        
        dialog = MCCurrencyDialog(self, field_type, existing_entries)
        if dialog.exec_() == QDialog.Accepted:
            entries = dialog.get_entries()
            self.mc_currency_details[field_type] = entries
            
            total = sum(e.get('total_php', 0) for e in entries)
            amount_field.setReadOnly(False)
            amount_field.setText(f"{total:,.2f}" if total > 0 else "")
            amount_field.setReadOnly(True)

            lotes_inputs = self.debit_lotes_inputs if field_type == "MC In" else self.credit_lotes_inputs
            if field_type in lotes_inputs:
                lotes_inputs[field_type].setText(str(len(entries)) if entries else "")

    def set_mc_currency_details(self, field_type, entries):

        self.mc_currency_details[field_type] = entries
        

        total = sum(e.get('total_php', 0) for e in entries)

        inputs = self.debit_inputs if field_type == "MC In" else self.credit_inputs
        if field_type in inputs:
            amount_field = inputs[field_type]
            amount_field.setReadOnly(False)
            amount_field.setText(f"{total:,.2f}" if total > 0 else "")
            amount_field.setReadOnly(True)
        

        lotes_inputs = self.debit_lotes_inputs if field_type == "MC In" else self.credit_lotes_inputs
        if field_type in lotes_inputs:
            lotes_inputs[field_type].setText(str(len(entries)) if entries else "")


    BANK_ACCOUNTS = [
        {"id": 1, "bank_name": "CIB-BDO", "account_name": "Global Reliance", "account_number": "0077-9002-3923"},
        {"id": 2, "bank_name": "CIB-BPI", "account_name": "Kristal Clear Diamond and Gold Pawnshop", "account_number": "0091-0692-29"},
        {"id": 3, "bank_name": "CIB-BDO", "account_name": "Kristal Clear", "account_number": "0077-9001-8784"},
        {"id": 4, "bank_name": "CIB-Union Bank", "account_name": "Golbal Reliance Mgmt and Holdings Corp", "account_number": "0015-6000-5790"},
        {"id": 5, "bank_name": "CIB-BDO", "account_name": "Europacific Management & Holdings Corp", "account_number": "0038-1801-5838"},
        {"id": 6, "bank_name": "CIB-BPI", "account_name": "Europacific Management & Holdings Corp", "account_number": "3541-0035-67"},
        {"id": 7, "bank_name": "CIB-UB", "account_name": "Europacific Management & Holdings Corp", "account_number": "0021-7001-7921"},
    ]

    def show_bank_account_selector(self):

        dialog = QDialog(self)
        dialog.setWindowTitle("Select Bank Account")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(300)
        
        layout = QVBoxLayout(dialog)
        
        
        header = QLabel("Select Bank Account for Fund Transfer")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #8B5CF6; padding: 10px;")
        layout.addWidget(header)
        

        list_widget = QListWidget()
        list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #F1F5F9;
            }
            QListWidget::item:selected {
                background-color: #8B5CF6;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #F3E8FF;
            }
        """)
        
        for bank in self.BANK_ACCOUNTS:
            item_text = f"{bank['bank_name']} - {bank['account_name']}"
            if bank.get('account_number'):
                item_text += f" ({bank['account_number']})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, bank['id'])
            item.setData(Qt.UserRole + 1, bank)
            list_widget.addItem(item)
            

            if self.selected_bank_account and self.selected_bank_account == bank['id']:
                list_widget.setCurrentItem(item)
        
        layout.addWidget(list_widget)
        

        btn_layout = QHBoxLayout()
        
        select_btn = QPushButton("✓ Select")
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6; color: white;
                border: none; border-radius: 5px;
                font-size: 12px; font-weight: 700;
                padding: 8px 20px;
            }
            QPushButton:hover { background-color: #7C3AED; }
        """)
        
        clear_btn = QPushButton("Clear Selection")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9; color: #64748B;
                border: 1px solid #E2E8F0; border-radius: 5px;
                font-size: 12px; font-weight: 600;
                padding: 8px 20px;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF; color: #64748B;
                border: 1px solid #E2E8F0; border-radius: 5px;
                font-size: 12px; font-weight: 600;
                padding: 8px 20px;
            }
            QPushButton:hover { background-color: #F8FAFC; }
        """)
        
        def on_select():
            current = list_widget.currentItem()
            if current:
                self.selected_bank_account = current.data(Qt.UserRole)
                bank_data = current.data(Qt.UserRole + 1)
                self.bank_account_btn.setText(f"{bank_data['bank_name'][:10]}")
                self.bank_account_btn.setToolTip(f"{bank_data['bank_name']} - {bank_data['account_name']}")
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "No Selection", "Please select a bank account.")
        
        def on_clear():
            self.selected_bank_account = None
            self.bank_account_btn.setText("Select Bank")
            self.bank_account_btn.setToolTip("Select bank account for fund transfer")
            dialog.accept()
        
        select_btn.clicked.connect(on_select)
        clear_btn.clicked.connect(on_clear)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(select_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec_()

    def create_money_input(self, placeholder=""):
   
        field = QLineEdit()
        field.setValidator(QDoubleValidator(0.0, 1e12, 2))
        field.setPlaceholderText(placeholder)
        field.setMaxLength(20)  # Limit to 20 characters for amount
        field.textChanged.connect(self.parent.recalculate_all)
        return field

    def create_lotes_input(self, placeholder="0"):

        field = QLineEdit()
        # Accept text input (not just integers) for PC lotes with 255 character limit
        field.setMaxLength(255)  # Limit to 255 characters for lotes text
        field.setPlaceholderText(placeholder)
        field.setMaximumWidth(_sz(80))
        field.setStyleSheet(
            f"background-color: #F8FAFC; border: 1px solid #E2E8F0; "
            f"border-radius: {_sz(5)}px; padding: {_sz(5)}px {_sz(10)}px; font-size: {_sz(14)}px; "
            f"color: #1E293B; font-weight: 600; min-height: {_sz(34)}px; min-width: {_sz(45)}px;"
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
  

        mapping = self._build_column_mapping()

        if field_name in mapping:
            return mapping[field_name]

    
        col = self._sanitize_column(field_name)
        print(f"[WARN] field_name_to_db_column: '{field_name}' not in config mapping, "
              f"using sanitized fallback '{col}'")
        return col

    def get_data(self):
      
        debit_values = {}
        for k, v in self.debit_inputs.items():
            text = v.text().strip().replace(",", "")  
            value = float(text) if text else 0
            db_column = self.field_name_to_db_column(k)
            debit_values[db_column] = value
            lotes_text = self.debit_lotes_inputs[k].text().strip()
            debit_values[db_column + "_lotes"] = int(lotes_text) if lotes_text else 0

        credit_values = {}
        for k, v in self.credit_inputs.items():
            text = v.text().strip().replace(",", "")  
            value = float(text) if text else 0
            db_column = self.field_name_to_db_column(k)
            credit_values[db_column] = value
            lotes_text = self.credit_lotes_inputs[k].text().strip()
            credit_values[db_column + "_lotes"] = int(lotes_text) if lotes_text else 0

        return {'debit': debit_values, 'credit': credit_values}

    def clear_fields(self):
  
        for field in list(self.debit_inputs.values()) + list(self.debit_lotes_inputs.values()) \
                     + list(self.credit_inputs.values()) + list(self.credit_lotes_inputs.values()):
            field.clear()

        self.mc_currency_details = {'MC In': [], 'MC Out': []}

    def get_raw_field_values(self) -> dict:
   
        out = {}
        for label, widget in self.debit_inputs.items():
            lotes_w = self.debit_lotes_inputs.get(label)
            branch_dest_w = self.branch_dest_inputs.get(label)
            out[f"debit::{label}"] = {
                "amount": widget.text(),
                "lotes": lotes_w.text() if lotes_w else "",
                "branch_dest": branch_dest_w.text() if branch_dest_w else ""
            }
        for label, widget in self.credit_inputs.items():
            lotes_w = self.credit_lotes_inputs.get(label)
            branch_dest_w = self.branch_dest_inputs.get(label)
            out[f"credit::{label}"] = {
                "amount": widget.text(),
                "lotes": lotes_w.text() if lotes_w else "",
                "branch_dest": branch_dest_w.text() if branch_dest_w else ""
            }
        return out

    def set_raw_field_values(self, data: dict):
    
        for key, val in data.items():
            section, label = key.split("::", 1)
            if section == "debit":
                widget = self.debit_inputs.get(label)
                lotes_w = self.debit_lotes_inputs.get(label)
                branch_dest_w = self.branch_dest_inputs.get(label)
            else:
                widget = self.credit_inputs.get(label)
                lotes_w = self.credit_lotes_inputs.get(label)
                branch_dest_w = self.branch_dest_inputs.get(label)
            if widget:
                widget.blockSignals(True)
                widget.setText(val.get("amount", ""))
                widget.blockSignals(False)
            if lotes_w:
                lotes_w.blockSignals(True)
                lotes_w.setText(val.get("lotes", ""))
                lotes_w.blockSignals(False)
            if branch_dest_w:
                branch_dest_w.blockSignals(True)
                branch_dest_w.setText(val.get("branch_dest", ""))
                branch_dest_w.blockSignals(False)
        self.parent.recalculate_all()

    def set_enabled(self, enabled):
  
        for field in list(self.debit_inputs.values()) + list(self.debit_lotes_inputs.values()) \
                     + list(self.credit_inputs.values()) + list(self.credit_lotes_inputs.values()):
            field.setEnabled(enabled)