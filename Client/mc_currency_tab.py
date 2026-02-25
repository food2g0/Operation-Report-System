from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QScrollArea, QFrame, QGridLayout,
    QComboBox, QPushButton
)
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtCore import Qt
import json


class MCCurrencyTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.currency_entries = []  # Store all currency entries
        self.grand_total_display = None  # Initialize to avoid AttributeError
        self.setup_ui()

    def setup_ui(self):
        """Setup the simplified MC Currency tab UI"""
        mc_scroll = QScrollArea()
        mc_scroll.setWidgetResizable(True)

        mc_widget = QWidget()
        mc_scroll.setWidget(mc_widget)

        mc_layout = QVBoxLayout(mc_widget)

        # Instructions section
        instructions_frame = QFrame()
        instructions_frame.setStyleSheet("""
            QFrame {
                background-color: #F0FDF4;
                border: 1px solid #BBF7D0;
                border-left: 4px solid #22C55E;
                border-radius: 8px;
                padding: 16px;
                margin: 10px 0;
            }
        """)
        instructions_layout = QVBoxLayout(instructions_frame)

        note_label = QLabel("\U0001F4B1 MC CURRENCY EXCHANGE")
        note_label.setStyleSheet("font-weight: 800; font-size: 14px; color: #166534; letter-spacing: 0.5px;")

        instruction_label = QLabel(
            "INSTRUCTIONS:\n"
            "\u2022 Select currency type from dropdown\n"
            "\u2022 Enter quantity (pieces)\n"
            "\u2022 Enter rate per unit\n"
            "\u2022 PHP Total will be calculated automatically\n"
            "\u2022 Example: 100 USD \u00d7 53.00 = \u20b15,300.00"
        )
        instruction_label.setStyleSheet("font-size: 11px; color: #166534; margin-top: 8px; line-height: 1.6;")
        instruction_label.setWordWrap(True)

        instructions_layout.addWidget(note_label)
        instructions_layout.addWidget(instruction_label)

        mc_layout.addWidget(instructions_frame)

        # Currency entries section
        self.entries_frame = QFrame()
        self.entries_layout = QVBoxLayout(self.entries_frame)

        # Add first entry by default
        self.add_currency_entry()

        mc_layout.addWidget(self.entries_frame)

        # Add/Remove buttons
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(buttons_frame)

        add_btn = QPushButton("\u2795 Add Currency Entry")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #22C55E;
                color: white;
                border: none;
                padding: 10px 18px;
                border-radius: 8px;
                font-weight: 700;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #16A34A;
            }
            QPushButton:pressed {
                background-color: #15803D;
            }
        """)
        add_btn.clicked.connect(self.add_currency_entry)

        remove_btn = QPushButton("\u2796 Remove Last Entry")
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #EF4444;
                border: 2px solid #EF4444;
                padding: 10px 18px;
                border-radius: 8px;
                font-weight: 700;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #FEF2F2;
            }
            QPushButton:pressed {
                background-color: #FEE2E2;
            }
        """)
        remove_btn.clicked.connect(self.remove_currency_entry)

        buttons_layout.addWidget(add_btn)
        buttons_layout.addWidget(remove_btn)
        buttons_layout.addStretch()

        mc_layout.addWidget(buttons_frame)

        # Summary section
        summary_frame = self.create_summary_section()
        mc_layout.addWidget(summary_frame)

        mc_layout.addStretch()

        # Create container widget and add scroll area
        container_layout = QVBoxLayout(self)
        container_layout.addWidget(mc_scroll)

    def add_currency_entry(self):
        """Add a new currency entry"""
        entry_num = len(self.currency_entries) + 1

        entry_frame = QFrame()
        entry_frame.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 12px;
                margin: 4px 0;
            }
        """)

        entry_layout = QHBoxLayout(entry_frame)

        # Entry number label
        num_label = QLabel(f"#{entry_num}")
        num_label.setStyleSheet("font-weight: 800; font-size: 13px; color: #3B82F6; min-width: 32px;")

        # Currency dropdown
        currency_combo = QComboBox()
        currency_combo.addItems([
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
        ])
        currency_combo.setStyleSheet("min-width: 180px; padding: 6px;")
        currency_combo.currentTextChanged.connect(self.calculate_totals)

        # Quantity input
        quantity_input = QLineEdit()
        quantity_input.setValidator(QIntValidator(0, 999999))
        quantity_input.setPlaceholderText("Pieces")
        quantity_input.setStyleSheet("min-width: 80px; padding: 6px;")
        quantity_input.textChanged.connect(self.calculate_totals)

        # Rate input
        rate_input = QLineEdit()
        rate_input.setValidator(QDoubleValidator(0.0, 999999.99, 2))
        rate_input.setPlaceholderText("Rate")
        rate_input.setStyleSheet("min-width: 100px; padding: 6px;")
        rate_input.textChanged.connect(self.calculate_totals)

        # PHP Total display
        php_total_display = QLabel("\u20b10.00")
        php_total_display.setStyleSheet("""
            background-color: #F0FDF4;
            border: 1px solid #BBF7D0;
            padding: 6px 12px;
            border-radius: 8px;
            min-width: 110px;
            font-weight: 800;
            font-size: 13px;
            color: #22C55E;
        """)

        # Layout
        entry_layout.addWidget(num_label)
        cur_lbl = QLabel("Currency:")
        cur_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748B;")
        entry_layout.addWidget(cur_lbl)
        entry_layout.addWidget(currency_combo)
        qty_lbl = QLabel("Qty:")
        qty_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748B;")
        entry_layout.addWidget(qty_lbl)
        entry_layout.addWidget(quantity_input)
        rate_lbl = QLabel("Rate:")
        rate_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748B;")
        entry_layout.addWidget(rate_lbl)
        entry_layout.addWidget(rate_input)
        php_lbl = QLabel("PHP Total:")
        php_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748B;")
        entry_layout.addWidget(php_lbl)
        entry_layout.addWidget(php_total_display)

        # Store entry data
        entry_data = {
            'frame': entry_frame,
            'currency_combo': currency_combo,
            'quantity_input': quantity_input,
            'rate_input': rate_input,
            'php_total_display': php_total_display,
            'number': entry_num
        }

        self.currency_entries.append(entry_data)
        self.entries_layout.addWidget(entry_frame)

        # Update calculations only if grand_total_display exists
        if hasattr(self, 'grand_total_display') and self.grand_total_display is not None:
            self.calculate_totals()

    def remove_currency_entry(self):
        """Remove the last currency entry"""
        if len(self.currency_entries) > 1:  # Keep at least one entry
            last_entry = self.currency_entries.pop()
            last_entry['frame'].setParent(None)
            last_entry['frame'].deleteLater()

            # Renumber remaining entries
            self.renumber_entries()
            self.calculate_totals()

    def renumber_entries(self):
        """Renumber all entries after removal"""
        for i, entry in enumerate(self.currency_entries):
            entry['number'] = i + 1
            # Find the number label (first widget in the layout)
            layout = entry['frame'].layout()
            num_label = layout.itemAt(0).widget()
            num_label.setText(f"#{i + 1}")

    def create_summary_section(self):
        """Create MC Currency summary section"""
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #F0FDF4;
                border: 1px solid #BBF7D0;
                border-radius: 12px;
                padding: 16px;
                margin: 10px 0;
            }
        """)

        summary_layout = QHBoxLayout(summary_frame)

        # Summary title
        summary_title = QLabel("\U0001F4B0 TOTAL MC CURRENCY:")
        summary_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #166534; letter-spacing: 0.3px;")

        # Grand total display
        self.grand_total_display = QLabel("\u20b10.00")
        self.grand_total_display.setStyleSheet("""
            font-size: 20px;
            font-weight: 800;
            color: #22C55E;
            background-color: #FFFFFF;
            padding: 10px 24px;
            border-radius: 10px;
            border: 1px solid #BBF7D0;
        """)

        summary_layout.addWidget(summary_title)
        summary_layout.addWidget(self.grand_total_display)
        summary_layout.addStretch()

        return summary_frame

    def calculate_totals(self):
        """Calculate totals for all currency entries"""
        grand_total = 0.0

        for entry in self.currency_entries:
            try:
                quantity = int(entry['quantity_input'].text().strip()) if entry['quantity_input'].text().strip() else 0
                rate = float(entry['rate_input'].text().strip()) if entry['rate_input'].text().strip() else 0.0

                php_total = quantity * rate
                entry['php_total_display'].setText(f"₱{php_total:,.2f}")

                grand_total += php_total

            except (ValueError, AttributeError):
                entry['php_total_display'].setText("₱0.00")

        # Only update grand_total_display if it exists
        if hasattr(self, 'grand_total_display') and self.grand_total_display is not None:
            self.grand_total_display.setText(f"₱{grand_total:,.2f}")

    def calculate_mc_totals(self):
        """Compatibility method - calls calculate_totals()"""
        self.calculate_totals()

    def get_data(self):
        """Get all data from MC Currency tab"""
        # Build numeric summary and a JSON details string for flexible storage
        grand_total = 0.0
        entries = []

        for entry in self.currency_entries:
            try:
                currency = entry['currency_combo'].currentText()
                quantity = int(entry['quantity_input'].text().strip()) if entry['quantity_input'].text().strip() else 0
                rate = float(entry['rate_input'].text().strip()) if entry['rate_input'].text().strip() else 0.0
                php_total = quantity * rate
            except (ValueError, AttributeError):
                currency = ""
                quantity = 0
                rate = 0.0
                php_total = 0.0

            entries.append({
                'currency': currency,
                'quantity': quantity,
                'rate': rate,
                'php_total': php_total
            })

            grand_total += php_total

        mc_values = {
            'mc_grand_total': float(grand_total),
            'mc_entries_count': int(len(self.currency_entries)),
            'mc_details': json.dumps(entries, ensure_ascii=False)
        }

        return mc_values

    def clear_fields(self):
        """Clear all MC Currency input fields"""
        # Clear all entries except the first one
        while len(self.currency_entries) > 1:
            self.remove_currency_entry()

        # Clear the remaining entry
        if self.currency_entries:
            entry = self.currency_entries[0]
            entry['currency_combo'].setCurrentIndex(0)
            entry['quantity_input'].clear()
            entry['rate_input'].clear()
            entry['php_total_display'].setText("₱0.00")

        # Only update grand_total_display if it exists
        if hasattr(self, 'grand_total_display') and self.grand_total_display is not None:
            self.grand_total_display.setText("₱0.00")