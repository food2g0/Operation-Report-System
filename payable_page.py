from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem,
    QDateEdit, QMessageBox, QHeaderView, QSizePolicy, QPushButton, QHBoxLayout,
    QApplication, QDesktopWidget, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont, QColor, QBrush, QTextDocument, QDoubleValidator
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from db_connect import db_manager
import datetime
from docx import Document


class PayablesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Palawan Transactions - Detailed View")

        # Get screen dimensions and maximize window
        self.setup_window_size()

        # Main layout with margins
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)
        self.setLayout(self.main_layout)

        # Create components
        self.create_controls()
        self.create_table()
        self.create_buttons()

        # Load data
        self.load_corporations()

        # Connect resize events
        self.installEventFilter(self)

    def setup_window_size(self):
        """Setup window to be maximized and responsive"""
        # Get the screen geometry
        desktop = QApplication.desktop()
        screen_geometry = desktop.screenGeometry()

        # Set minimum size to ensure usability on smaller screens
        self.setMinimumSize(1200, 700)

        # Maximize the window
        self.showMaximized()

    def create_controls(self):
        """Create responsive group headers and corporation/date selectors"""
        # Create a frame for controls with better styling
        controls_frame = QFrame()
        controls_frame.setFrameStyle(QFrame.Box)
        controls_frame.setLineWidth(1)
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
            }
        """)

        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setSpacing(15)

        # Second row - corporation and date selectors
        selectors_layout = QHBoxLayout()
        selectors_layout.setSpacing(20)

        # Corporation selector with improved styling
        corp_label = QLabel("Corporation:")
        corp_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.corp_selector = QComboBox()
        self.corp_selector.setMinimumWidth(200)
        self.corp_selector.setMaximumWidth(300)
        self.corp_selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.corp_selector.currentTextChanged.connect(self.populate_table)
        self.corp_selector.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
                font-size: 11px;
            }
            QComboBox:focus {
                border-color: #007bff;
            }
        """)

        # Date selector with improved styling
        date_label = QLabel("Date:")
        date_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.date_selector = QDateEdit(calendarPopup=True)
        self.date_selector.setDate(QDate.currentDate())
        self.date_selector.setDisplayFormat("yyyy-MM-dd")
        self.date_selector.setMinimumWidth(150)
        self.date_selector.setMaximumWidth(200)
        self.date_selector.dateChanged.connect(self.populate_table)
        self.date_selector.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
                font-size: 11px;
            }
            QDateEdit:focus {
                border-color: #007bff;
            }
        """)

        selectors_layout.addWidget(corp_label)
        selectors_layout.addWidget(self.corp_selector)
        selectors_layout.addSpacing(30)
        selectors_layout.addWidget(date_label)
        selectors_layout.addWidget(self.date_selector)
        selectors_layout.addStretch()

        controls_layout.addLayout(selectors_layout)
        self.main_layout.addWidget(controls_frame)

        self.create_group_headers_layout(controls_layout)

    def create_group_headers_layout(self, parent_layout):
        """Create responsive group headers that adjust to screen size"""
        self.headers_layout = QHBoxLayout()
        self.headers_layout.setSpacing(0)

        # Store header widgets for responsive adjustments
        self.header_widgets = []

        # Create visual group headers with responsive sizing
        headers_data = [
            ("Branches", "#495057", "#f8f9fa", 1),
            ("PALAWAN SEND-OUT", "#dc3545", "#fff", 5),
            ("PALAWAN PAY-OUT", "#28a745", "#fff", 5),
            ("PALAWAN INTERNATIONAL", "#007bff", "#fff", 5),
            ("ADJUSTMENTS", "#6f42c1", "#fff", 4)
        ]

        for text, color, bg_color, column_count in headers_data:
            label = QLabel(text)
            label.setStyleSheet(f"""
                font-weight: bold; 
                text-align: center; 
                padding: 12px; 
                background-color: {bg_color}; 
                border: 1px solid #dee2e6; 
                color: {color}; 
                border-left: 4px solid {color};
                font-size: 11px;
            """)
            label.setAlignment(Qt.AlignCenter)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            # Store reference for responsive adjustments
            label.column_count = column_count
            self.header_widgets.append(label)
            self.headers_layout.addWidget(label)

        parent_layout.addLayout(self.headers_layout)

    def adjust_header_widths(self):
        """Adjust header widths based on current table column widths"""
        if not hasattr(self, 'table') or not hasattr(self, 'header_widgets'):
            return

        # Calculate total available width
        table_width = self.table.width()

        # Adjust each header based on its column count and current table column widths
        current_col = 0
        for header in self.header_widgets:
            total_width = 0
            for i in range(header.column_count):
                if current_col < self.table.columnCount():
                    total_width += self.table.columnWidth(current_col)
                    current_col += 1

            # Set the header width to match its columns
            if total_width > 0:
                header.setFixedWidth(max(total_width, 100))  # Minimum width of 100

    def create_table(self):
        """Create responsive main table with grouped headers"""
        # Create scroll area for better responsiveness
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.table = QTableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Set the number of columns
        total_columns = 20  # 1 + (5 * 3) + 4
        self.table.setColumnCount(total_columns)

        # Set headers
        sub_headers = [
            "Branches",
            # Palawan Send Out (5 columns)
            "Lotes", "Capital", "SC", "Commission", "Total",
            # Palawan Pay Out (5 columns)
            "Lotes", "Capital", "SC", "Commission", "Total",
            # Palawan INTERNATIONAL (5 columns)
            "Lotes", "Capital", "SC", "Commission", "Total",
            # Manual fields (4 columns)
            "SKID", "SKIR", "CANCELLATION", "INC"
        ]

        self.table.setHorizontalHeaderLabels(sub_headers)

        # Setup responsive column behavior
        self.setup_responsive_columns()

        # Style the table
        self.style_table_with_grouped_headers()

        # Connect item changed signal for real-time updates
        self.table.itemChanged.connect(self.on_item_changed)

        scroll_area.setWidget(self.table)
        self.main_layout.addWidget(scroll_area)

    def setup_responsive_columns(self):
        """Setup responsive column widths"""
        header = self.table.horizontalHeader()

        # Branch column - resize to contents but with limits
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setColumnWidth(0, 120)  # Set minimum width

        # Data columns - start with fixed widths but allow stretching
        base_width = 80
        for i in range(1, self.table.columnCount()):
            self.table.setColumnWidth(i, base_width)
            header.setSectionResizeMode(i, QHeaderView.Interactive)

        # Enable horizontal stretching for the last few columns
        header.setStretchLastSection(False)

        # Use a timer to adjust widths after the widget is fully rendered
        QTimer.singleShot(100, self.adjust_responsive_widths)

    def adjust_responsive_widths(self):
        """Adjust column widths based on available space"""
        if not self.table.isVisible():
            return

        # Get available width
        available_width = self.table.viewport().width()
        current_total_width = sum(self.table.columnWidth(i) for i in range(self.table.columnCount()))

        # If we have extra space, distribute it proportionally
        if available_width > current_total_width:
            extra_width = available_width - current_total_width
            # Distribute extra width among data columns (not branch column)
            data_columns = self.table.columnCount() - 1
            extra_per_column = extra_width // data_columns

            for i in range(1, self.table.columnCount()):
                current_width = self.table.columnWidth(i)
                new_width = min(current_width + extra_per_column, 120)  # Max width limit
                self.table.setColumnWidth(i, new_width)

        # Update header widths to match
        self.adjust_header_widths()

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        # Delay the width adjustment to avoid excessive calls during resize
        if hasattr(self, 'resize_timer'):
            self.resize_timer.stop()
        else:
            self.resize_timer = QTimer()
            self.resize_timer.setSingleShot(True)
            self.resize_timer.timeout.connect(self.adjust_responsive_widths)

        self.resize_timer.start(150)  # 150ms delay

    def style_table_with_grouped_headers(self):
        """Enhanced table styling for better visual appeal"""
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                border: 1px solid #c0c0c0;
                background-color: white;
                alternate-background-color: #f8f9fa;
                font-size: 10px;
                selection-background-color: #e3f2fd;
            }
            QTableWidget::item {
                border: 1px solid #e0e0e0;
                padding: 8px 4px;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
            QTableWidget::item:focus {
                background-color: #bbdefb;
                border: 2px solid #2196f3;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                border: 1px solid #d0d0d0;
                padding: 10px 5px;
                font-weight: bold;
                text-align: center;
                color: #333;
                font-size: 10px;
            }
            QHeaderView::section:hover {
                background-color: #e8e8e8;
            }
        """)

        # Enable alternating row colors
        self.table.setAlternatingRowColors(True)

    def on_item_changed(self, item):
        """Handle item changes for real-time updates"""
        row = item.row()
        col = item.column()

        # Only handle adjustment columns
        if col >= 16 and col <= 19:
            try:
                # Validate input
                value = float(item.text()) if item.text() else 0.0
                item.setText(f"{value:.2f}")
                self.calculate_adjustment_totals()
                # Auto-save adjustment changes
                self.save_single_row_adjustments(row)
            except ValueError:
                item.setText("0.00")
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")

    def create_buttons(self):
        """Create responsive export, print, and save buttons"""
        button_frame = QFrame()
        button_frame.setMaximumHeight(60)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 10, 0, 10)

        # Create buttons with better styling
        button_style = """
            QPushButton {
                padding: 12px 24px;
                border: 2px solid #007bff;
                border-radius: 6px;
                background-color: #007bff;
                color: white;
                font-weight: bold;
                font-size: 11px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #0056b3;
                border-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """

        # Save to Database button
        self.save_button = QPushButton("💾 Save to Database")
        self.save_button.clicked.connect(self.save_to_database)
        self.save_button.setStyleSheet(
            button_style.replace("#007bff", "#28a745").replace("#0056b3", "#1e7e34").replace("#004085", "#155724"))

        self.export_button = QPushButton("📄 Export to Word")
        self.export_button.clicked.connect(self.export_to_word)
        self.export_button.setStyleSheet(button_style)

        self.print_button = QPushButton("🖨️ Print Report")
        self.print_button.clicked.connect(self.print_table)
        self.print_button.setStyleSheet(
            button_style.replace("#007bff", "#6f42c1").replace("#0056b3", "#5a2d91").replace("#004085", "#4c1f75"))

        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addSpacing(15)
        button_layout.addWidget(self.export_button)
        button_layout.addSpacing(15)
        button_layout.addWidget(self.print_button)
        button_layout.addStretch()

        self.main_layout.addWidget(button_frame)

    def load_corporations(self):
        """Load unique corporations from the daily_reports table"""
        self.corp_selector.clear()
        try:
            query = "SELECT DISTINCT corporation FROM daily_reports ORDER BY corporation"
            corporations = db_manager.execute_query(query)

            for corp in corporations:
                self.corp_selector.addItem(corp['corporation'])

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error loading corporations: {str(e)}")

    def populate_table(self):
        """Populate table with detailed Palawan transaction data and existing payable data"""
        corp = self.corp_selector.currentText()
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")

        if not corp:
            return

        try:
            # Query to get all Palawan data from daily_reports
            daily_query = """
                          SELECT branch,
                                 -- Send Out data
                                 COALESCE(palawan_sendout_lotes_total, 0)         as so_lotes,
                                 COALESCE(palawan_sendout_principal, 0)           as so_capital,
                                 COALESCE(palawan_sendout_sc, 0)                  as so_sc,
                                 COALESCE(palawan_sendout_commission, 0)          as so_commission,
                                 COALESCE(palawan_sendout_regular_total, 0)       as so_total,

                                 -- Pay Out data  
                                 COALESCE(palawan_payout_lotes_total, 0)          as po_lotes,
                                 COALESCE(palawan_payout_principal, 0)            as po_capital,
                                 COALESCE(palawan_payout_sc, 0)                   as po_sc,
                                 COALESCE(palawan_payout_commission, 0)           as po_commission,
                                 COALESCE(palawan_payout_regular_total, 0)        as po_total,

                                 -- International data
                                 COALESCE(palawan_international_lotes_total, 0)   as int_lotes,
                                 COALESCE(palawan_international_principal, 0)     as int_capital,
                                 COALESCE(palawan_international_sc, 0)            as int_sc,
                                 COALESCE(palawan_international_commission, 0)    as int_commission,
                                 COALESCE(palawan_international_regular_total, 0) as int_total

                          FROM daily_reports
                          WHERE corporation = %s
                            AND date = %s
                          ORDER BY branch \
                          """

            # Query to get existing adjustment data from payable_tbl
            payable_query = """
                            SELECT branch, skid, skir, cancellation, inc
                            FROM payable_tbl
                            WHERE corporation = %s \
                              AND date = %s \
                            """

            results = db_manager.execute_query(daily_query, (corp, selected_date))
            payable_results = db_manager.execute_query(payable_query, (corp, selected_date))

            # Convert payable results to dictionary for easy lookup
            payable_data = {}
            if payable_results:
                for row in payable_results:
                    if isinstance(row, dict):
                        payable_data[row['branch']] = {
                            'skid': float(row['skid']),
                            'skir': float(row['skir']),
                            'cancellation': float(row['cancellation']),
                            'inc': float(row['inc'])
                        }
                    elif isinstance(row, (list, tuple)) and len(row) >= 5:
                        payable_data[row[0]] = {
                            'skid': float(row[1]),
                            'skir': float(row[2]),
                            'cancellation': float(row[3]),
                            'inc': float(row[4])
                        }

            self.table.setRowCount(0)

            if not results:
                QMessageBox.information(self, "No Data", f"No data found for {selected_date}.")
                return

            # Totals for each column
            column_totals = [0.0] * (self.table.columnCount() - 1)  # Exclude branch column
            row_count = 0

            for row_data in results:
                self.table.insertRow(row_count)

                # Branch name
                branch_name = row_data['branch'] if isinstance(row_data, dict) else row_data[0]
                self.table.setItem(row_count, 0, QTableWidgetItem(branch_name))

                # Data in the exact order as your table
                if isinstance(row_data, dict):
                    values = [
                        # Send Out: Lotes, Capital, SC, Commission, Total
                        float(row_data['so_lotes']),
                        float(row_data['so_capital']),
                        float(row_data['so_sc']),
                        float(row_data['so_commission']),
                        float(row_data['so_total']),

                        # Pay Out: Lotes, Capital, SC, Commission, Total
                        float(row_data['po_lotes']),
                        float(row_data['po_capital']),
                        float(row_data['po_sc']),
                        float(row_data['po_commission']),
                        float(row_data['po_total']),

                        # International: Lotes, Capital, SC, Commission, Total
                        float(row_data['int_lotes']),
                        float(row_data['int_capital']),
                        float(row_data['int_sc']),
                        float(row_data['int_commission']),
                        float(row_data['int_total'])
                    ]
                else:
                    # Handle tuple/list format
                    values = [float(x) for x in row_data[1:16]]  # Skip branch name

                # Add values to table and accumulate totals
                for i, value in enumerate(values, 1):  # Start from column 1 (skip branch)
                    self.table.setItem(row_count, i, QTableWidgetItem(f"{value:.2f}"))
                    column_totals[i - 1] += value

                # Adjustment fields (SKID, SKIR, CANCELLATION, INC) - load from payable_tbl or default to 0
                adjustment_values = [0.0, 0.0, 0.0, 0.0]
                if branch_name in payable_data:
                    adjustment_values = [
                        payable_data[branch_name]['skid'],
                        payable_data[branch_name]['skir'],
                        payable_data[branch_name]['cancellation'],
                        payable_data[branch_name]['inc']
                    ]

                for i, adj_value in enumerate(adjustment_values):
                    col_index = 16 + i  # Columns 16-19
                    item = QTableWidgetItem(f"{adj_value:.2f}")
                    item.setFlags(item.flags() | Qt.ItemIsEditable)  # Make editable
                    self.table.setItem(row_count, col_index, item)
                    column_totals[col_index - 1] += adj_value

                row_count += 1

            # Add totals row
            self.add_totals_row(column_totals)

            # Add visual group headers and colors
            self.add_group_headers_visual()

            # Adjust responsive widths after population
            QTimer.singleShot(200, self.adjust_responsive_widths)

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error loading data: {str(e)}")

    def add_totals_row(self, column_totals):
        """Add totals row to the table"""
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)

        # Style for totals row
        total_font = QFont()
        total_font.setBold(True)
        total_brush = QBrush(QColor("#e9ecef"))

        # Branch column
        total_item = QTableWidgetItem("TOTAL")
        total_item.setFont(total_font)
        total_item.setBackground(total_brush)
        total_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row_count, 0, total_item)

        # All columns totals
        for i, total in enumerate(column_totals, 1):
            total_item = QTableWidgetItem(f"{total:.2f}")
            total_item.setFont(total_font)
            total_item.setBackground(total_brush)
            total_item.setTextAlignment(Qt.AlignCenter)
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)  # Make totals row non-editable
            self.table.setItem(row_count, i, total_item)

    def add_group_headers_visual(self):
        """Add enhanced visual highlighting for different data groups"""
        if self.table.rowCount() == 0:
            return

        # Enhanced colors for better visual distinction
        colors = {
            'sendout_total': QColor("#ffebee"),  # Light red
            'payout_total': QColor("#e8f5e8"),  # Light green
            'intl_total': QColor("#e3f2fd"),  # Light blue
            'adjustment': QColor("#f3e5f5"),  # Light purple
            'totals_row': QColor("#e9ecef"),  # Light gray
            'totals_highlight': QColor("#ffc107")  # Warning yellow
        }

        for row in range(self.table.rowCount()):
            is_totals_row = (row == self.table.rowCount() - 1)

            # Highlight total columns for each section
            section_totals = [5, 10, 15]  # Total columns
            for col in section_totals:
                item = self.table.item(row, col)
                if item:
                    if is_totals_row:
                        item.setBackground(QBrush(colors['totals_highlight']))
                        item.setFont(QFont("", 0, QFont.Bold))
                    else:
                        if col == 5:  # Sendout total
                            item.setBackground(QBrush(colors['sendout_total']))
                        elif col == 10:  # Payout total
                            item.setBackground(QBrush(colors['payout_total']))
                        elif col == 15:  # International total
                            item.setBackground(QBrush(colors['intl_total']))

            # Highlight editable adjustment columns
            for col in range(16, 20):
                item = self.table.item(row, col)
                if item:
                    if is_totals_row:
                        item.setBackground(QBrush(colors['totals_row']))
                        item.setFont(QFont("", 0, QFont.Bold))
                    else:
                        item.setBackground(QBrush(colors['adjustment']))

            # Special styling for branch name in totals row
            if is_totals_row:
                branch_item = self.table.item(row, 0)
                if branch_item:
                    branch_item.setBackground(QBrush(colors['totals_row']))
                    branch_item.setFont(QFont("", 0, QFont.Bold))

    def calculate_adjustment_totals(self):
        """Calculate totals for adjustment columns with improved error handling"""
        if self.table.rowCount() == 0:
            return

        totals_row = self.table.rowCount() - 1

        # Calculate totals for each adjustment column
        for col in range(16, 20):  # SKID, SKIR, CANCELLATION, INC
            total = 0.0

            # Sum up all values in this column (excluding totals row)
            for row in range(totals_row):
                item = self.table.item(row, col)
                if item and item.text():
                    try:
                        value = float(item.text())
                        total += value
                    except ValueError:
                        # If invalid value, reset to 0
                        item.setText("0.00")

            # Update the totals row
            total_item = self.table.item(totals_row, col)
            if total_item:
                total_item.setText(f"{total:.2f}")
                # Highlight if total is non-zero
                if abs(total) > 0.01:  # Use small epsilon for float comparison
                    total_item.setBackground(QBrush(QColor("#fff3cd")))
                else:
                    total_item.setBackground(QBrush(QColor("#e9ecef")))

    def save_to_database(self):
        """Save all Palawan transaction totals to payable_tbl"""
        corp = self.corp_selector.currentText()
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")

        if not corp or self.table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "No data to save.")
            return

        try:
            saved_count = 0
            updated_count = 0
            error_count = 0

            # Process each row (excluding totals row)
            totals_row = self.table.rowCount() - 1

            for row in range(totals_row):
                branch_item = self.table.item(row, 0)
                if not branch_item:
                    continue

                branch = branch_item.text()

                # Extract data from table
                try:
                    # Palawan Send Out data (columns 2-4: Capital, SC, Commission)
                    sendout_capital = float(self.table.item(row, 2).text()) if self.table.item(row, 2) else 0.0
                    sendout_sc = float(self.table.item(row, 3).text()) if self.table.item(row, 3) else 0.0
                    sendout_commission = float(self.table.item(row, 4).text()) if self.table.item(row, 4) else 0.0
                    sendout_total = float(self.table.item(row, 5).text()) if self.table.item(row, 5) else 0.0

                    # Palawan Pay Out data (columns 7-9: Capital, SC, Commission)
                    payout_capital = float(self.table.item(row, 7).text()) if self.table.item(row, 7) else 0.0
                    payout_sc = float(self.table.item(row, 8).text()) if self.table.item(row, 8) else 0.0
                    payout_commission = float(self.table.item(row, 9).text()) if self.table.item(row, 9) else 0.0
                    payout_total = float(self.table.item(row, 10).text()) if self.table.item(row, 10) else 0.0

                    # Palawan International data (columns 12-14: Capital, SC, Commission)
                    international_capital = float(self.table.item(row, 12).text()) if self.table.item(row, 12) else 0.0
                    international_sc = float(self.table.item(row, 13).text()) if self.table.item(row, 13) else 0.0
                    international_commission = float(self.table.item(row, 14).text()) if self.table.item(row,
                                                                                                         14) else 0.0
                    international_total = float(self.table.item(row, 15).text()) if self.table.item(row, 15) else 0.0

                    # Adjustment data (columns 16-19: SKID, SKIR, CANCELLATION, INC)
                    skid = float(self.table.item(row, 16).text()) if self.table.item(row, 16) else 0.0
                    skir = float(self.table.item(row, 17).text()) if self.table.item(row, 17) else 0.0
                    cancellation = float(self.table.item(row, 18).text()) if self.table.item(row, 18) else 0.0
                    inc = float(self.table.item(row, 19).text()) if self.table.item(row, 19) else 0.0

                except (ValueError, AttributeError) as e:
                    print(f"Error parsing data for branch {branch}: {e}")
                    error_count += 1
                    continue

                # Use INSERT ... ON DUPLICATE KEY UPDATE to handle duplicates
                query = """
                        INSERT INTO payable_tbl (corporation, branch, date, \
                                                 sendout_capital, sendout_sc, sendout_commission, sendout_total, \
                                                 payout_capital, payout_sc, payout_commission, payout_total, \
                                                 international_capital, international_sc, international_commission, \
                                                 international_total, \
                                                 skid, skir, cancellation, inc) \
                        VALUES (%s, %s, %s, \
                                %s, %s, %s, %s, \
                                %s, %s, %s, %s, \
                                %s, %s, %s, %s, \
                                %s, %s, %s, %s) ON DUPLICATE KEY \
                        UPDATE \
                            sendout_capital = \
                        VALUES (sendout_capital), sendout_sc = \
                        VALUES (sendout_sc), sendout_commission = \
                        VALUES (sendout_commission), sendout_total = \
                        VALUES (sendout_total), payout_capital = \
                        VALUES (payout_capital), payout_sc = \
                        VALUES (payout_sc), payout_commission = \
                        VALUES (payout_commission), payout_total = \
                        VALUES (payout_total), international_capital = \
                        VALUES (international_capital), international_sc = \
                        VALUES (international_sc), international_commission = \
                        VALUES (international_commission), international_total = \
                        VALUES (international_total), skid = \
                        VALUES (skid), skir = \
                        VALUES (skir), cancellation = \
                        VALUES (cancellation), inc = \
                        VALUES (inc), updated_at = CURRENT_TIMESTAMP \
                        """

                params = (
                    corp, branch, selected_date,
                    sendout_capital, sendout_sc, sendout_commission, sendout_total,
                    payout_capital, payout_sc, payout_commission, payout_total,
                    international_capital, international_sc, international_commission, international_total,
                    skid, skir, cancellation, inc
                )

                try:
                    # Check if record exists to determine if it's insert or update
                    check_query = "SELECT COUNT(*) as count FROM payable_tbl WHERE corporation = %s AND branch = %s AND date = %s"
                    check_result = db_manager.execute_query(check_query, (corp, branch, selected_date))

                    if check_result:
                        if isinstance(check_result[0], dict):
                            exists = check_result[0]['count'] > 0
                        else:
                            exists = check_result[0][0] > 0
                    else:
                        exists = False

                    # Execute the insert/update query
                    db_manager.execute_query(query, params)

                    if exists:
                        updated_count += 1
                    else:
                        saved_count += 1

                except Exception as e:
                    print(f"Error saving data for branch {branch}: {e}")
                    error_count += 1
                    continue

            # Show success message
            message = f"Save Operation Complete!\n\n"
            message += f"New records saved: {saved_count}\n"
            message += f"Existing records updated: {updated_count}\n"
            if error_count > 0:
                message += f"Errors encountered: {error_count}\n"
            message += f"\nCorporation: {corp}\n"
            message += f"Date: {selected_date}"

            QMessageBox.information(self, "Save Successful", message)

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error saving to database: {str(e)}")

    def save_single_row_adjustments(self, row):
        """Save adjustments for a single row when values change"""
        if row >= self.table.rowCount() - 1:  # Skip totals row
            return

        corp = self.corp_selector.currentText()
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")

        branch_item = self.table.item(row, 0)
        if not branch_item or not corp:
            return

        branch = branch_item.text()

        try:
            # Get adjustment values
            skid = float(self.table.item(row, 16).text()) if self.table.item(row, 16) else 0.0
            skir = float(self.table.item(row, 17).text()) if self.table.item(row, 17) else 0.0
            cancellation = float(self.table.item(row, 18).text()) if self.table.item(row, 18) else 0.0
            inc = float(self.table.item(row, 19).text()) if self.table.item(row, 19) else 0.0

            # Check if record exists
            check_query = "SELECT id FROM payable_tbl WHERE corporation = %s AND branch = %s AND date = %s"
            check_result = db_manager.execute_query(check_query, (corp, branch, selected_date))

            if check_result:
                # Update existing record - only adjustment fields
                update_query = """
                               UPDATE payable_tbl
                               SET skid         = %s, \
                                   skir         = %s, \
                                   cancellation = %s, \
                                   inc          = %s, \
                                   updated_at   = CURRENT_TIMESTAMP
                               WHERE corporation = %s \
                                 AND branch = %s \
                                 AND date = %s \
                               """
                db_manager.execute_query(update_query, (skid, skir, cancellation, inc, corp, branch, selected_date))
            else:
                # If no record exists, we need to save the full row first
                # This will be handled by the main save_to_database function
                pass

        except Exception as e:
            print(f"Error auto-saving adjustments for branch {branch}: {e}")

    def export_to_word(self):
        """Export table data to Word document with better formatting"""
        try:
            document = Document()

            # Add title with better formatting
            title = document.add_heading('Detailed Palawan Transaction Report', 0)
            title.alignment = 1  # Center alignment

            # Add metadata
            corp = self.corp_selector.currentText()
            date = self.date_selector.date().toString("yyyy-MM-dd")

            info_para = document.add_paragraph()
            info_para.add_run(f"Corporation: ").bold = True
            info_para.add_run(f"{corp}\n")
            info_para.add_run(f"Date: ").bold = True
            info_para.add_run(f"{date}\n")
            info_para.add_run(f"Generated: ").bold = True
            info_para.add_run(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            rows = self.table.rowCount()
            cols = self.table.columnCount()

            if rows == 0:
                QMessageBox.warning(self, "No Data", "No data to export.")
                return

            # Create table with header row
            word_table = document.add_table(rows=rows + 1, cols=cols)
            word_table.style = 'Light Grid Accent 1'

            # Add headers
            header_cells = word_table.rows[0].cells
            for col in range(cols):
                header_item = self.table.horizontalHeaderItem(col)
                header_cells[col].text = header_item.text() if header_item else ""
                # Make header bold
                for paragraph in header_cells[col].paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True

            # Add data
            for row in range(rows):
                table_cells = word_table.rows[row + 1].cells
                for col in range(cols):
                    item = self.table.item(row, col)
                    table_cells[col].text = item.text() if item else ""

                    # Make totals row bold
                    if row == rows - 1:  # Last row (totals)
                        for paragraph in table_cells[col].paragraphs:
                            for run in paragraph.runs:
                                run.font.bold = True

            # Save with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Palawan_Report_{corp}_{date}_{timestamp}.docx"
            document.save(filename)

            QMessageBox.information(self, "Export Successful",
                                    f"Report exported successfully!\n\nFile: {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting to Word: {str(e)}")

    def print_table(self):
        """Enhanced print functionality with better formatting"""
        try:
            if self.table.rowCount() == 0:
                QMessageBox.warning(self, "No Data", "No data to print.")
                return

            doc = QTextDocument()

            # Enhanced HTML styling
            html = """
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h2 { color: #2c3e50; text-align: center; margin-bottom: 10px; }
                    .info { margin-bottom: 20px; font-size: 12px; }
                    table { 
                        border-collapse: collapse; 
                        width: 100%; 
                        font-size: 9px;
                        margin: 0 auto;
                    }
                    th, td { 
                        border: 1px solid #ddd; 
                        padding: 4px 6px; 
                        text-align: center; 
                    }
                    th { 
                        background-color: #f8f9fa; 
                        font-weight: bold; 
                        color: #495057;
                    }
                    .totals-row { 
                        background-color: #e9ecef; 
                        font-weight: bold; 
                    }
                    .sendout-total { background-color: #ffebee; }
                    .payout-total { background-color: #e8f5e8; }
                    .intl-total { background-color: #e3f2fd; }
                    .adjustment { background-color: #f3e5f5; }
                </style>
            </head>
            <body>
            """

            html += "<h2>Detailed Palawan Transaction Report</h2>"
            html += f"""
            <div class="info">
                <strong>Corporation:</strong> {self.corp_selector.currentText()}<br>
                <strong>Date:</strong> {self.date_selector.date().toString('yyyy-MM-dd')}<br>
                <strong>Generated:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
            """

            html += "<table>"

            # Add headers
            html += "<tr>"
            for col in range(self.table.columnCount()):
                header_item = self.table.horizontalHeaderItem(col)
                header_text = header_item.text() if header_item else ""
                html += f"<th>{header_text}</th>"
            html += "</tr>"

            # Add data rows with enhanced styling
            for row in range(self.table.rowCount()):
                is_totals_row = (row == self.table.rowCount() - 1)
                row_class = "totals-row" if is_totals_row else ""
                html += f"<tr class='{row_class}'>"

                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    cell_text = item.text() if item else ""

                    # Add special styling for different column types
                    cell_class = ""
                    if not is_totals_row:
                        if col == 5:  # Sendout total
                            cell_class = "sendout-total"
                        elif col == 10:  # Payout total
                            cell_class = "payout-total"
                        elif col == 15:  # International total
                            cell_class = "intl-total"
                        elif 16 <= col <= 19:  # Adjustment columns
                            cell_class = "adjustment"

                    html += f"<td class='{cell_class}'>{cell_text}</td>"
                html += "</tr>"

            html += "</table></body></html>"
            doc.setHtml(html)

            printer = QPrinter()
            printer.setPageSize(QPrinter.A4)
            printer.setPageMargins(10, 10, 10, 10, QPrinter.Millimeter)

            dialog = QPrintDialog(printer, self)
            if dialog.exec_() == QPrintDialog.Accepted:
                doc.print_(printer)
                QMessageBox.information(self, "Print Successful", "Report printed successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Error printing: {str(e)}")

    def showEvent(self, event):
        """Handle show event to ensure proper initial sizing"""
        super().showEvent(event)
        # Delay the adjustment to ensure the widget is fully rendered
        QTimer.singleShot(300, self.adjust_responsive_widths)

    def update_totals(self):
        """Update totals after populating data"""
        # This method is called after initial population
        # The adjustment totals will be calculated as users edit the fields
        self.calculate_adjustment_totals()


# Additional utility functions for better responsiveness
def get_optimal_font_size(widget_width):
    """Calculate optimal font size based on widget width"""
    if widget_width < 1200:
        return 9
    elif widget_width < 1600:
        return 10
    else:
        return 11


def apply_responsive_styling(widget, screen_width):
    """Apply responsive styling based on screen width"""
    if screen_width < 1366:  # Small screens
        base_font_size = 9
        padding = "6px"
    elif screen_width < 1920:  # Medium screens
        base_font_size = 10
        padding = "8px"
    else:  # Large screens
        base_font_size = 11
        padding = "10px"

    return f"font-size: {base_font_size}px; padding: {padding};"