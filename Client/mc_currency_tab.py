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
        self.currency_entries = [] 
        self.grand_total_display = None  
        self.buying_total_display = None
        self.selling_total_display = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the simplified MC Currency tab UI"""
        mc_scroll = QScrollArea()
        mc_scroll.setWidgetResizable(True)

        mc_widget = QWidget()
        mc_scroll.setWidget(mc_widget)

        mc_layout = QVBoxLayout(mc_widget)


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
            "\u2022 Enter pieces (quantity of bills)\n"
            "\u2022 Enter denomination (bill value, e.g. 100 for $100 bill)\n"
            "\u2022 Enter rate per unit\n"
            "\u2022 PHP Total = Pcs × Denomination × Rate\n"
            "\u2022 Example: 2 pcs × 100 USD × 58.00 = ₱11,600.00"
        )
        instruction_label.setStyleSheet("font-size: 13px; color: #166534; margin-top: 8px; line-height: 1.6;")
        instruction_label.setWordWrap(True)

        instructions_layout.addWidget(note_label)
        instructions_layout.addWidget(instruction_label)

        mc_layout.addWidget(instructions_frame)


        self.entries_frame = QFrame()
        self.entries_layout = QVBoxLayout(self.entries_frame)


        self.add_currency_entry()

        mc_layout.addWidget(self.entries_frame)


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


        quantity_input = QLineEdit()
        quantity_input.setValidator(QIntValidator(0, 999999))
        quantity_input.setPlaceholderText("Pcs")
        quantity_input.setStyleSheet("min-width: 60px; padding: 6px;")
        quantity_input.textChanged.connect(self.calculate_totals)

  
        denomination_input = QLineEdit()
        denomination_input.setValidator(QDoubleValidator(0.0, 999999.99, 2))
        denomination_input.setPlaceholderText("Denom")
        denomination_input.setStyleSheet("min-width: 70px; padding: 6px;")
        denomination_input.textChanged.connect(self.calculate_totals)

        # Rate input
        rate_input = QLineEdit()
        rate_input.setValidator(QDoubleValidator(0.0, 999999.99, 2))
        rate_input.setPlaceholderText("Rate")
        rate_input.setStyleSheet("min-width: 80px; padding: 6px;")
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

        # Buy/Sell type dropdown
        type_combo = QComboBox()
        type_combo.addItems(["Buying", "Selling"])
        type_combo.setStyleSheet("""
            QComboBox {
                min-width: 90px;
                padding: 6px;
                font-weight: 600;
            }
        """)
        type_combo.currentTextChanged.connect(self.calculate_totals)

  
        entry_layout.addWidget(num_label)
        cur_lbl = QLabel("Currency:")
        cur_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B;")
        entry_layout.addWidget(cur_lbl)
        entry_layout.addWidget(currency_combo)
        qty_lbl = QLabel("Pcs:")
        qty_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B;")
        entry_layout.addWidget(qty_lbl)
        entry_layout.addWidget(quantity_input)
        denom_lbl = QLabel("Denom:")
        denom_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B;")
        entry_layout.addWidget(denom_lbl)
        entry_layout.addWidget(denomination_input)
        rate_lbl = QLabel("Rate:")
        rate_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B;")
        entry_layout.addWidget(rate_lbl)
        entry_layout.addWidget(rate_input)
        php_lbl = QLabel("Total:")
        php_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B;")
        entry_layout.addWidget(php_lbl)
        entry_layout.addWidget(php_total_display)
        type_lbl = QLabel("Type:")
        type_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B;")
        entry_layout.addWidget(type_lbl)
        entry_layout.addWidget(type_combo)

        # Store entry data
        entry_data = {
            'frame': entry_frame,
            'currency_combo': currency_combo,
            'quantity_input': quantity_input,
            'denomination_input': denomination_input,
            'rate_input': rate_input,
            'php_total_display': php_total_display,
            'type_combo': type_combo,
            'number': entry_num
        }

        self.currency_entries.append(entry_data)
        self.entries_layout.addWidget(entry_frame)


        if hasattr(self, 'grand_total_display') and self.grand_total_display is not None:
            self.calculate_totals()

    def remove_currency_entry(self):
        """Remove the last currency entry"""
        if len(self.currency_entries) > 1:  # Keep at least one entry
            last_entry = self.currency_entries.pop()
            last_entry['frame'].setParent(None)
            last_entry['frame'].deleteLater()

            self.renumber_entries()
            self.calculate_totals()

    def renumber_entries(self):
 
        for i, entry in enumerate(self.currency_entries):
            entry['number'] = i + 1
            # Find the number label (first widget in the layout)
            layout = entry['frame'].layout()
            num_label = layout.itemAt(0).widget()
            num_label.setText(f"#{i + 1}")

    def create_summary_section(self):
        """Create MC Currency summary section with Buying (MC Out) and Selling (MC In) totals"""
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

        summary_layout = QVBoxLayout(summary_frame)
        
        # Title row
        title_label = QLabel("\U0001F4B0 MC CURRENCY SUMMARY")
        title_label.setStyleSheet("font-size: 14px; font-weight: 800; color: #166534; letter-spacing: 0.3px;")
        summary_layout.addWidget(title_label)
        
        # Totals row
        totals_row = QHBoxLayout()
        
        # Buying total (MC Out)
        buying_frame = QFrame()
        buying_layout = QVBoxLayout(buying_frame)
        buying_title = QLabel("BUYING (MC Out):")
        buying_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #DC2626;")
        self.buying_total_display = QLabel("\u20b10.00")
        self.buying_total_display.setStyleSheet("""
            font-size: 16px;
            font-weight: 800;
            color: #DC2626;
            background-color: #FEF2F2;
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid #FECACA;
        """)
        buying_layout.addWidget(buying_title)
        buying_layout.addWidget(self.buying_total_display)
        
        # Selling total (MC In)
        selling_frame = QFrame()
        selling_layout = QVBoxLayout(selling_frame)
        selling_title = QLabel("SELLING (MC In):")
        selling_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #22C55E;")
        self.selling_total_display = QLabel("\u20b10.00")
        self.selling_total_display.setStyleSheet("""
            font-size: 16px;
            font-weight: 800;
            color: #22C55E;
            background-color: #F0FDF4;
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid #BBF7D0;
        """)
        selling_layout.addWidget(selling_title)
        selling_layout.addWidget(self.selling_total_display)
        
        # Grand total
        grand_frame = QFrame()
        grand_layout = QVBoxLayout(grand_frame)
        grand_title = QLabel("GRAND TOTAL:")
        grand_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #3B82F6;")
        self.grand_total_display = QLabel("\u20b10.00")
        self.grand_total_display.setStyleSheet("""
            font-size: 16px;
            font-weight: 800;
            color: #3B82F6;
            background-color: #EFF6FF;
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid #BFDBFE;
        """)
        grand_layout.addWidget(grand_title)
        grand_layout.addWidget(self.grand_total_display)
        
        totals_row.addWidget(buying_frame)
        totals_row.addWidget(selling_frame)
        totals_row.addWidget(grand_frame)
        totals_row.addStretch()
        
        summary_layout.addLayout(totals_row)

        return summary_frame

    def calculate_totals(self):
        """Calculate totals for all currency entries, separated by buying/selling"""
        grand_total = 0.0
        buying_total = 0.0
        selling_total = 0.0

        for entry in self.currency_entries:
            try:
                quantity = int(entry['quantity_input'].text().strip()) if entry['quantity_input'].text().strip() else 0
                denomination = float(entry['denomination_input'].text().strip()) if entry['denomination_input'].text().strip() else 0.0
                rate = float(entry['rate_input'].text().strip()) if entry['rate_input'].text().strip() else 0.0
                entry_type = entry['type_combo'].currentText()

                # Total = Pcs × Denomination × Rate
                php_total = quantity * denomination * rate
                entry['php_total_display'].setText(f"₱{php_total:,.2f}")
                
                # Color code based on type
                if entry_type == "Buying":
                    entry['php_total_display'].setStyleSheet("""
                        background-color: #FEF2F2;
                        border: 1px solid #FECACA;
                        padding: 6px 12px;
                        border-radius: 8px;
                        min-width: 110px;
                        font-weight: 800;
                        font-size: 13px;
                        color: #DC2626;
                    """)
                    buying_total += php_total
                else:  # Selling
                    entry['php_total_display'].setStyleSheet("""
                        background-color: #F0FDF4;
                        border: 1px solid #BBF7D0;
                        padding: 6px 12px;
                        border-radius: 8px;
                        min-width: 110px;
                        font-weight: 800;
                        font-size: 13px;
                        color: #22C55E;
                    """)
                    selling_total += php_total

                grand_total += php_total

            except (ValueError, AttributeError):
                entry['php_total_display'].setText("₱0.00")

        # Update displays if they exist
        if hasattr(self, 'buying_total_display') and self.buying_total_display is not None:
            self.buying_total_display.setText(f"₱{buying_total:,.2f}")
        if hasattr(self, 'selling_total_display') and self.selling_total_display is not None:
            self.selling_total_display.setText(f"₱{selling_total:,.2f}")
        if hasattr(self, 'grand_total_display') and self.grand_total_display is not None:
            self.grand_total_display.setText(f"₱{grand_total:,.2f}")
        
        # Update MC In/MC Out fields in cash flow tabs
        self._update_cash_flow_mc_fields(selling_total, buying_total)

    def _update_cash_flow_mc_fields(self, mc_in_value, mc_out_value):
        """Update MC In (selling) and MC Out (buying) fields in cash flow tabs"""
        try:
            # Update Brand A cash flow tab
            if hasattr(self.parent, 'cash_flow_tab_a'):
                cf_a = self.parent.cash_flow_tab_a
                # MC In is a debit field (selling - money coming in)
                if 'MC In' in cf_a.debit_inputs:
                    widget = cf_a.debit_inputs['MC In']
                    widget.blockSignals(True)
                    widget.setText(f"{mc_in_value:.2f}" if mc_in_value > 0 else "")
                    widget.blockSignals(False)
                # MC Out is a credit field (buying - money going out)
                if 'MC Out' in cf_a.credit_inputs:
                    widget = cf_a.credit_inputs['MC Out']
                    widget.blockSignals(True)
                    widget.setText(f"{mc_out_value:.2f}" if mc_out_value > 0 else "")
                    widget.blockSignals(False)
            
            # Update Brand B cash flow tab
            if hasattr(self.parent, 'cash_flow_tab_b'):
                cf_b = self.parent.cash_flow_tab_b
                # MC In is a debit field (selling - money coming in)
                if 'MC In' in cf_b.debit_inputs:
                    widget = cf_b.debit_inputs['MC In']
                    widget.blockSignals(True)
                    widget.setText(f"{mc_in_value:.2f}" if mc_in_value > 0 else "")
                    widget.blockSignals(False)
                # MC Out is a credit field (buying - money going out)
                if 'MC Out' in cf_b.credit_inputs:
                    widget = cf_b.credit_inputs['MC Out']
                    widget.blockSignals(True)
                    widget.setText(f"{mc_out_value:.2f}" if mc_out_value > 0 else "")
                    widget.blockSignals(False)
            
            # Trigger recalculation
            if hasattr(self.parent, 'recalculate_all'):
                self.parent.recalculate_all()
        except Exception as e:
            print(f"Error updating MC fields: {e}")

    def calculate_mc_totals(self):
        """Compatibility method - calls calculate_totals()"""
        self.calculate_totals()

    def get_data(self):
        """Get all data from MC Currency tab with separate buying/selling totals"""
        # Build numeric summary and a JSON details string for flexible storage
        grand_total = 0.0
        buying_total = 0.0  # MC Out
        selling_total = 0.0  # MC In
        entries = []

        for entry in self.currency_entries:
            try:
                currency = entry['currency_combo'].currentText()
                quantity = int(entry['quantity_input'].text().strip()) if entry['quantity_input'].text().strip() else 0
                denomination = float(entry['denomination_input'].text().strip()) if entry['denomination_input'].text().strip() else 0.0
                rate = float(entry['rate_input'].text().strip()) if entry['rate_input'].text().strip() else 0.0
                entry_type = entry['type_combo'].currentText()
                # Total = Pcs × Denomination × Rate
                php_total = quantity * denomination * rate
            except (ValueError, AttributeError):
                currency = ""
                quantity = 0
                denomination = 0.0
                rate = 0.0
                entry_type = "Buying"
                php_total = 0.0

            entries.append({
                'currency': currency,
                'quantity': quantity,
                'denomination': denomination,
                'rate': rate,
                'type': entry_type,
                'php_total': php_total
            })

            grand_total += php_total
            if entry_type == "Buying":
                buying_total += php_total
            else:
                selling_total += php_total

        mc_values = {
            'mc_grand_total': float(grand_total),
            'mc_in': float(selling_total),   # Selling = MC In (money coming in)
            'mc_out': float(buying_total),   # Buying = MC Out (money going out)
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
            entry['denomination_input'].clear()
            entry['rate_input'].clear()
            entry['type_combo'].setCurrentIndex(0)
            entry['php_total_display'].setText("₱0.00")

        # Update all displays if they exist
        if hasattr(self, 'buying_total_display') and self.buying_total_display is not None:
            self.buying_total_display.setText("₱0.00")
        if hasattr(self, 'selling_total_display') and self.selling_total_display is not None:
            self.selling_total_display.setText("₱0.00")
        if hasattr(self, 'grand_total_display') and self.grand_total_display is not None:
            self.grand_total_display.setText("₱0.00")