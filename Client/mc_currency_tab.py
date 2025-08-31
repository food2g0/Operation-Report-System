from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QScrollArea, QFrame, QGridLayout,
    QComboBox, QPushButton
)
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtCore import Qt


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
                background-color: #e8f5e8;
                border-left: 4px solid #28a745;
                border-radius: 4px;
                padding: 15px;
                margin: 10px 0;
            }
        """)
        instructions_layout = QVBoxLayout(instructions_frame)

        note_label = QLabel("💱 MC CURRENCY EXCHANGE")
        note_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #155724;")

        instruction_label = QLabel(
            "INSTRUCTIONS:\n"
            "• Select currency type from dropdown\n"
            "• Enter quantity (pieces)\n"
            "• Enter rate per unit\n"
            "• PHP Total will be calculated automatically\n"
            "• Example: 100 USD × 53.00 = ₱5,300.00"
        )
        instruction_label.setStyleSheet("font-size: 11px; color: #155724; margin-top: 8px;")
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

        add_btn = QPushButton("➕ Add Currency Entry")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_btn.clicked.connect(self.add_currency_entry)

        remove_btn = QPushButton("➖ Remove Last Entry")
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
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
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                margin: 5px 0;
            }
        """)

        entry_layout = QHBoxLayout(entry_frame)

        # Entry number label
        num_label = QLabel(f"#{entry_num}")
        num_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #495057; min-width: 30px;")

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
        currency_combo.setStyleSheet("min-width: 180px; padding: 5px;")
        currency_combo.currentTextChanged.connect(self.calculate_totals)

        # Quantity input
        quantity_input = QLineEdit()
        quantity_input.setValidator(QIntValidator(0, 999999))
        quantity_input.setPlaceholderText("Pieces")
        quantity_input.setStyleSheet("min-width: 80px; padding: 5px;")
        quantity_input.textChanged.connect(self.calculate_totals)

        # Rate input
        rate_input = QLineEdit()
        rate_input.setValidator(QDoubleValidator(0.0, 999999.99, 2))
        rate_input.setPlaceholderText("Rate")
        rate_input.setStyleSheet("min-width: 100px; padding: 5px;")
        rate_input.textChanged.connect(self.calculate_totals)

        # PHP Total display
        php_total_display = QLabel("₱0.00")
        php_total_display.setStyleSheet("""
            background-color: white;
            border: 1px solid #ced4da;
            padding: 5px 10px;
            border-radius: 3px;
            min-width: 100px;
            font-weight: bold;
            color: #28a745;
        """)

        # Layout
        entry_layout.addWidget(num_label)
        entry_layout.addWidget(QLabel("Currency:"))
        entry_layout.addWidget(currency_combo)
        entry_layout.addWidget(QLabel("Qty:"))
        entry_layout.addWidget(quantity_input)
        entry_layout.addWidget(QLabel("Rate:"))
        entry_layout.addWidget(rate_input)
        entry_layout.addWidget(QLabel("PHP Total:"))
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
                background-color: white;
                border: 2px solid #28a745;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
            }
        """)

        summary_layout = QHBoxLayout(summary_frame)

        # Summary title
        summary_title = QLabel("💰 TOTAL MC CURRENCY:")
        summary_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #28a745;")

        # Grand total display
        self.grand_total_display = QLabel("₱0.00")
        self.grand_total_display.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #28a745;
            background-color: #e8f5e8;
            padding: 10px 20px;
            border-radius: 5px;
            border: 2px solid #28a745;
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
        mc_values = {
            'mc_grand_total': 0.0,
            'mc_entries_count': len(self.currency_entries)
        }

        grand_total = 0.0

        for i, entry in enumerate(self.currency_entries, 1):
            try:
                currency = entry['currency_combo'].currentText()
                quantity = int(entry['quantity_input'].text().strip()) if entry['quantity_input'].text().strip() else 0
                rate = float(entry['rate_input'].text().strip()) if entry['rate_input'].text().strip() else 0.0
                php_total = quantity * rate

                # Store individual entry data
                mc_values[f'mc_entry_{i}_currency'] = currency
                mc_values[f'mc_entry_{i}_quantity'] = quantity
                mc_values[f'mc_entry_{i}_rate'] = rate
                mc_values[f'mc_entry_{i}_php_total'] = php_total

                grand_total += php_total

            except (ValueError, AttributeError):
                mc_values[f'mc_entry_{i}_currency'] = ""
                mc_values[f'mc_entry_{i}_quantity'] = 0
                mc_values[f'mc_entry_{i}_rate'] = 0.0
                mc_values[f'mc_entry_{i}_php_total'] = 0.0

        mc_values['mc_grand_total'] = grand_total

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