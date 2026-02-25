from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QScrollArea, QFrame, QGridLayout
)
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import Qt


class PalawanDetailsTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """Setup the Palawan details tab UI"""
        palawan_scroll = QScrollArea()
        palawan_scroll.setWidgetResizable(True)

        palawan_widget = QWidget()
        palawan_scroll.setWidget(palawan_widget)

        palawan_layout = QVBoxLayout(palawan_widget)

    

        # Create main sections
        main_sections_frame = QFrame()
        main_sections_layout = QGridLayout(main_sections_frame)
        main_sections_layout.setSpacing(15)

        # Palawan Send Out
        sendout_group = self.create_palawan_section_group(
            "PALAWAN SEND-OUT",
            "sendout",
            "#1b75bc"
        )

        # Palawan Pay Out
        payout_group = self.create_palawan_section_group(
            "PALAWAN PAY-OUT",
            "payout",
            "#1b75bc"
        )

        # Palawan International
        international_group = self.create_palawan_section_group(
            "PALAWAN INTERNATIONAL",
            "international",
            "#1b75bc"
        )

        main_sections_layout.addWidget(sendout_group, 0, 0)
        main_sections_layout.addWidget(payout_group, 0, 1)
        main_sections_layout.addWidget(international_group, 1, 0, 1, 2)

        palawan_layout.addWidget(main_sections_frame)

        # Add Lotes section
        lotes_section = self.create_lotes_section()
        palawan_layout.addWidget(lotes_section)

        palawan_layout.addStretch()

        # Create container widget and add scroll area
        container_layout = QVBoxLayout(self)
        container_layout.addWidget(palawan_scroll)

    def create_palawan_section_group(self, title, section_type, color):
        """Create a Palawan section group with improved styling"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                margin-top: 18px;
                padding: 18px 16px 14px 16px;
                background-color: #FFFFFF;
            }}
            QGroupBox::title {{
                color: {color};
                font-weight: 800;
                font-size: 11px;
                letter-spacing: 1.2px;
                padding: 2px 10px;
                background-color: #FFFFFF;
                border-radius: 4px;
            }}
        """)

        form = QFormLayout()
        form.setSpacing(10)
        form.setContentsMargins(16, 24, 16, 16)

        # Create input dictionary
        inputs = {}

        # Regular fields
        fields = [("Principal", "Enter Principal"), ("SC", "Enter SC"), ("Commission", "Enter Commission")]

        for label_text, placeholder in fields:
            field = self.create_money_input(placeholder)
            field.textChanged.connect(self.calculate_palawan_totals)
            label = QLabel(label_text + ":")
            label.setStyleSheet("font-size: 12px; font-weight: 600; color: #334155;")
            form.addRow(label, field)
            inputs[label_text] = field

        # Section total
        total_display = self.parent.create_display_field("0.00")
        total_display.setStyleSheet(
            f"font-weight: 800; font-size: 14px; color: {color}; "
            f"background-color: #F0F9FF; border: 1px solid #BAE6FD; "
            f"border-radius: 8px; padding: 8px 12px;"
        )
        total_lbl = QLabel("TOTAL:")
        total_lbl.setStyleSheet(f"font-weight: 700; color: {color}; font-size: 12px;")
        form.addRow(total_lbl, total_display)

        group.setLayout(form)

        # Store references using the section type
        setattr(self, f"{section_type}_inputs", inputs)
        setattr(self, f"{section_type}_total_display", total_display)

        return group

    def create_lotes_section(self):
        """Create the Lotes section with fields for each Palawan type"""
        lotes_group = QGroupBox("LOTES TRANSACTIONS")
        lotes_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                margin-top: 18px;
                padding: 18px 16px 14px 16px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                color: #8B5CF6;
                font-weight: 800;
                font-size: 11px;
                letter-spacing: 1.2px;
                padding: 2px 10px;
                background-color: #FFFFFF;
                border-radius: 4px;
            }
        """)

        form = QFormLayout()
        form.setSpacing(10)
        form.setContentsMargins(16, 24, 16, 16)

        # Create lotes input dictionary
        self.lotes_inputs = {}

        # Lotes fields for each section
        lotes_fields = [
            ("Lotes Send-Out", "Enter Lotes Send-Out Amount"),
            ("Lotes Pay-Out", "Enter Lotes Pay-Out Amount"),
            ("Lotes International", "Enter Lotes International Amount")
        ]

        for label_text, placeholder in lotes_fields:
            field = self.create_money_input(placeholder)
            field.textChanged.connect(self.calculate_lotes_total)
            label = QLabel(label_text + ":")
            label.setStyleSheet("font-size: 12px; font-weight: 600; color: #334155;")
            form.addRow(label, field)
            self.lotes_inputs[label_text] = field

        # Lotes total
        self.lotes_total_display = self.parent.create_display_field("0.00")
        self.lotes_total_display.setStyleSheet(
            "font-weight: 800; font-size: 14px; color: #8B5CF6; "
            "background-color: #F5F3FF; border: 1px solid #DDD6FE; "
            "border-radius: 8px; padding: 8px 12px;"
        )
        total_lbl = QLabel("LOTES TOTAL:")
        total_lbl.setStyleSheet("font-weight: 700; color: #8B5CF6; font-size: 12px;")
        form.addRow(total_lbl, self.lotes_total_display)

        lotes_group.setLayout(form)
        return lotes_group

    def create_money_input(self, placeholder=""):
        """Create money input field"""
        field = QLineEdit()
        field.setValidator(QDoubleValidator(0.0, 1e12, 2))
        field.setPlaceholderText(placeholder)
        field.textChanged.connect(self.parent.recalculate_all)
        return field

    def calculate_palawan_totals(self):
        """Calculate totals for each Palawan section"""
        sections = ['sendout', 'payout', 'international']

        for section in sections:
            inputs = getattr(self, f"{section}_inputs", {})
            total = self.parent.get_total_amount(inputs)
            display = getattr(self, f"{section}_total_display", None)
            if display:
                display.setText(f"{total:.2f}")

    def calculate_lotes_total(self):
        """Calculate total for Lotes section"""
        lotes_total = self.parent.get_total_amount(self.lotes_inputs)
        self.lotes_total_display.setText(f"{lotes_total:.2f}")

    def get_data(self):
        """Get all data from Palawan tab"""
        palawan_values = {}

        # Send Out data (regular)
        for k, v in self.sendout_inputs.items():
            value = float(v.text().strip()) if v.text().strip() else 0
            palawan_values[f"palawan_sendout_{k.lower()}"] = value
        palawan_values["palawan_sendout_regular_total"] = float(
            self.sendout_total_display.text().strip()) if self.sendout_total_display.text().strip() else 0

        # Pay Out data (regular)
        for k, v in self.payout_inputs.items():
            value = float(v.text().strip()) if v.text().strip() else 0
            palawan_values[f"palawan_payout_{k.lower()}"] = value
        palawan_values["palawan_payout_regular_total"] = float(
            self.payout_total_display.text().strip()) if self.payout_total_display.text().strip() else 0

        # International data (regular)
        for k, v in self.international_inputs.items():
            value = float(v.text().strip()) if v.text().strip() else 0
            palawan_values[f"palawan_international_{k.lower()}"] = value
        palawan_values["palawan_international_regular_total"] = float(
            self.international_total_display.text().strip()) if self.international_total_display.text().strip() else 0

        # Lotes data - map to existing database columns
        lotes_mapping = {
            "Lotes Send-Out": "palawan_sendout_lotes_total",
            "Lotes Pay-Out": "palawan_payout_lotes_total",
            "Lotes International": "palawan_international_lotes_total"
        }

        for k, v in self.lotes_inputs.items():
            value = float(v.text().strip()) if v.text().strip() else 0
            if k in lotes_mapping:
                palawan_values[lotes_mapping[k]] = value

        return palawan_values

    def clear_fields(self):
        """Clear all Palawan input fields"""
        # Clear Send Out fields
        for field in getattr(self, 'sendout_inputs', {}).values():
            field.clear()

        # Clear Pay Out fields
        for field in getattr(self, 'payout_inputs', {}).values():
            field.clear()

        # Clear International fields
        for field in getattr(self, 'international_inputs', {}).values():
            field.clear()

        # Clear Lotes fields
        for field in getattr(self, 'lotes_inputs', {}).values():
            field.clear()