"""
User Management Page for Admin Dashboard
Manages corporations, branches, and client accounts with pagination
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QMessageBox, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QDialogButtonBox,
    QSpinBox, QTabWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from db_connect_pooled import db_manager
from admin_manage import create_corporation, create_branch, create_client
from security import hash_password


class UserManagementPage(QWidget):
    """Page for managing corporations, branches, and client accounts"""
    
    def __init__(self):
        super().__init__()
        self.db = db_manager
        
        # Pagination state
        self.corp_page = 0
        self.branch_page = 0
        self.client_page = 0
        self.page_size = 10
        
        # Data cache
        self.corp_total = 0
        self.branch_total = 0
        self.client_total = 0
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user management UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Title
        title = QLabel("⚙️ User Management")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        main_layout.addWidget(title)

        # Tab widget for different sections
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #dee2e6; border-radius: 4px; background: white; }
            QTabBar::tab { background: #f8f9fa; padding: 8px 20px; margin-right: 2px; border: 1px solid #dee2e6; border-bottom: none; border-radius: 4px 4px 0 0; }
            QTabBar::tab:selected { background: white; font-weight: bold; }
            QTabBar::tab:hover { background: #e9ecef; }
        """)
        
        # Create tabs
        self.tabs.addTab(self._build_corporations_tab(), "📊 Corporations")
        self.tabs.addTab(self._build_branches_tab(), "🏢 Branches")
        self.tabs.addTab(self._build_clients_tab(), "👥 Clients")
        self.tabs.addTab(self._build_admin_users_tab(), "👑 Admin Users")
        
        # Auto-refresh dropdowns when switching tabs
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        main_layout.addWidget(self.tabs)
        
        # Load corporation dropdowns (for branch and client forms)
        self._load_corp_dropdowns()

    def _build_corporations_tab(self):
        """Build corporations management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # Add form
        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background: #f8f9fa; border-radius: 6px; padding: 10px; }")
        form_layout = QHBoxLayout(form_frame)
        
        self.corp_name_input = QLineEdit()
        self.corp_name_input.setPlaceholderText("Enter corporation name")
        self.corp_name_input.setMinimumWidth(250)
        
        add_btn = QPushButton("➕ Add")
        add_btn.setStyleSheet("QPushButton { background: #27ae60; color: white; padding: 6px 16px; border: none; border-radius: 4px; font-weight: bold; } QPushButton:hover { background: #219a52; }")
        add_btn.clicked.connect(self._add_corporation)
        
        form_layout.addWidget(QLabel("Name:"))
        form_layout.addWidget(self.corp_name_input)
        form_layout.addWidget(add_btn)
        form_layout.addStretch()
        
        layout.addWidget(form_frame)

        # Table with pagination
        table_frame = QFrame()
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # Control bar
        control_bar = QHBoxLayout()
        show_btn = QPushButton("📋 Show Corporations")
        show_btn.setStyleSheet("QPushButton { background: #3498db; color: white; padding: 6px 16px; border: none; border-radius: 4px; font-weight: bold; } QPushButton:hover { background: #2980b9; }")
        show_btn.clicked.connect(self._load_corporations)
        
        self.corp_page_label = QLabel("Page 0 of 0")
        prev_btn = QPushButton("◀")
        prev_btn.setFixedWidth(40)
        prev_btn.clicked.connect(lambda: self._change_corp_page(-1))
        next_btn = QPushButton("▶")
        next_btn.setFixedWidth(40)
        next_btn.clicked.connect(lambda: self._change_corp_page(1))
        
        control_bar.addWidget(show_btn)
        control_bar.addStretch()
        control_bar.addWidget(prev_btn)
        control_bar.addWidget(self.corp_page_label)
        control_bar.addWidget(next_btn)
        
        table_layout.addLayout(control_bar)
        
        # Table
        self.corp_table = QTableWidget()
        self.corp_table.setColumnCount(4)
        self.corp_table.setHorizontalHeaderLabels(["ID", "Corporation Name", "Created At", "Actions"])
        self.corp_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.corp_table.setAlternatingRowColors(True)
        self.corp_table.setStyleSheet("""
            QTableWidget { background: white; gridline-color: #dee2e6; border: 1px solid #dee2e6; font-size: 11px; }
            QTableWidget::item { padding: 5px; }
            QHeaderView::section { background: #f8f9fa; padding: 8px; border: none; border-bottom: 2px solid #dee2e6; font-weight: bold; }
        """)
        header = self.corp_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        table_layout.addWidget(self.corp_table)
        layout.addWidget(table_frame)
        
        return widget

    def _build_branches_tab(self):
        """Build branches management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # Add form
        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background: #f8f9fa; border-radius: 6px; padding: 10px; }")
        form_layout = QHBoxLayout(form_frame)
        
        self.branch_corp_combo = QComboBox()
        self.branch_corp_combo.setMinimumWidth(150)
        
        self.branch_name_input = QLineEdit()
        self.branch_name_input.setPlaceholderText("Enter branch name")
        self.branch_name_input.setMinimumWidth(200)

        self.branch_os_input = QLineEdit()
        self.branch_os_input.setPlaceholderText("Operation Supervisor name")
        self.branch_os_input.setMinimumWidth(180)
        
        add_btn = QPushButton("➕ Add")
        add_btn.setStyleSheet("QPushButton { background: #27ae60; color: white; padding: 6px 16px; border: none; border-radius: 4px; font-weight: bold; } QPushButton:hover { background: #219a52; }")
        add_btn.clicked.connect(self._add_branch)
        
        form_layout.addWidget(QLabel("Corporation:"))
        form_layout.addWidget(self.branch_corp_combo)
        form_layout.addWidget(QLabel("Branch Name:"))
        form_layout.addWidget(self.branch_name_input)
        form_layout.addWidget(QLabel("OS:"))
        form_layout.addWidget(self.branch_os_input)
        form_layout.addWidget(add_btn)
        form_layout.addStretch()
        
        layout.addWidget(form_frame)

        # Table with pagination
        table_frame = QFrame()
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # Control bar
        control_bar = QHBoxLayout()
        show_btn = QPushButton("📋 Show Branches")
        show_btn.setStyleSheet("QPushButton { background: #3498db; color: white; padding: 6px 16px; border: none; border-radius: 4px; font-weight: bold; } QPushButton:hover { background: #2980b9; }")
        show_btn.clicked.connect(self._load_branches)
        
        # Corporation filter dropdown
        filter_label = QLabel("Filter by Corp:")
        self.branch_filter_combo = QComboBox()
        self.branch_filter_combo.setMinimumWidth(150)
        self.branch_filter_combo.addItem("All Corporations", None)
        self.branch_filter_combo.currentIndexChanged.connect(self._on_branch_filter_changed)
        
        self.branch_page_label = QLabel("Page 0 of 0")
        prev_btn = QPushButton("◀")
        prev_btn.setFixedWidth(40)
        prev_btn.clicked.connect(lambda: self._change_branch_page(-1))
        next_btn = QPushButton("▶")
        next_btn.setFixedWidth(40)
        next_btn.clicked.connect(lambda: self._change_branch_page(1))
        
        control_bar.addWidget(show_btn)
        control_bar.addSpacing(20)
        control_bar.addWidget(filter_label)
        control_bar.addWidget(self.branch_filter_combo)
        control_bar.addStretch()
        control_bar.addWidget(prev_btn)
        control_bar.addWidget(self.branch_page_label)
        control_bar.addWidget(next_btn)
        
        table_layout.addLayout(control_bar)
        
        # Table
        self.branch_table = QTableWidget()
        self.branch_table.setColumnCount(7)
        self.branch_table.setHorizontalHeaderLabels(["ID", "Branch Name", "Corporation", "OS", "Created At", "Registered", "Actions"])
        self.branch_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.branch_table.setAlternatingRowColors(True)
        self.branch_table.setStyleSheet("""
            QTableWidget { background: white; gridline-color: #dee2e6; border: 1px solid #dee2e6; font-size: 11px; }
            QTableWidget::item { padding: 5px; }
            QHeaderView::section { background: #f8f9fa; padding: 8px; border: none; border-bottom: 2px solid #dee2e6; font-weight: bold; }
        """)
        header = self.branch_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        table_layout.addWidget(self.branch_table)
        layout.addWidget(table_frame)
        
        return widget

    def _build_clients_tab(self):
        """Build clients management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # Add form
        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background: #f8f9fa; border-radius: 6px; padding: 10px; }")
        form_layout = QVBoxLayout(form_frame)
        
        # Row 1
        row1 = QHBoxLayout()
        self.client_first_input = QLineEdit()
        self.client_first_input.setPlaceholderText("First name")
        self.client_first_input.setMinimumWidth(120)
        self.client_last_input = QLineEdit()
        self.client_last_input.setPlaceholderText("Last name")
        self.client_last_input.setMinimumWidth(120)
        self.client_corp_combo = QComboBox()
        self.client_corp_combo.setMinimumWidth(150)
        self.client_corp_combo.currentIndexChanged.connect(self._on_client_corp_changed)
        self.client_branch_combo = QComboBox()
        self.client_branch_combo.setMinimumWidth(150)
        
        row1.addWidget(QLabel("First:"))
        row1.addWidget(self.client_first_input)
        row1.addWidget(QLabel("Last:"))
        row1.addWidget(self.client_last_input)
        row1.addWidget(QLabel("Corp:"))
        row1.addWidget(self.client_corp_combo)
        row1.addWidget(QLabel("Branch:"))
        row1.addWidget(self.client_branch_combo)
        
        # Row 2
        row2 = QHBoxLayout()
        self.client_password_input = QLineEdit()
        self.client_password_input.setPlaceholderText("Password")
        self.client_password_input.setEchoMode(QLineEdit.Password)
        self.client_password_input.setMinimumWidth(150)
        
        add_btn = QPushButton("➕ Add Client")
        add_btn.setStyleSheet("QPushButton { background: #27ae60; color: white; padding: 6px 16px; border: none; border-radius: 4px; font-weight: bold; } QPushButton:hover { background: #219a52; }")
        add_btn.clicked.connect(self._add_client)
        
        row2.addWidget(QLabel("Password:"))
        row2.addWidget(self.client_password_input)
        row2.addWidget(add_btn)
        row2.addStretch()
        
        form_layout.addLayout(row1)
        form_layout.addLayout(row2)
        layout.addWidget(form_frame)

        # Table with pagination
        table_frame = QFrame()
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # Control bar
        control_bar = QHBoxLayout()
        show_btn = QPushButton("📋 Show Clients")
        show_btn.setStyleSheet("QPushButton { background: #3498db; color: white; padding: 6px 16px; border: none; border-radius: 4px; font-weight: bold; } QPushButton:hover { background: #2980b9; }")
        show_btn.clicked.connect(self._load_clients)
        
        # Search
        self.client_search_input = QLineEdit()
        self.client_search_input.setPlaceholderText("Search by username or name...")
        self.client_search_input.setMaximumWidth(200)
        self.client_search_input.returnPressed.connect(self._load_clients)
        
        self.client_page_label = QLabel("Page 0 of 0")
        prev_btn = QPushButton("◀")
        prev_btn.setFixedWidth(40)
        prev_btn.clicked.connect(lambda: self._change_client_page(-1))
        next_btn = QPushButton("▶")
        next_btn.setFixedWidth(40)
        next_btn.clicked.connect(lambda: self._change_client_page(1))
        
        control_bar.addWidget(show_btn)
        control_bar.addWidget(self.client_search_input)
        control_bar.addStretch()
        control_bar.addWidget(prev_btn)
        control_bar.addWidget(self.client_page_label)
        control_bar.addWidget(next_btn)
        
        table_layout.addLayout(control_bar)
        
        # Table
        self.client_table = QTableWidget()
        self.client_table.setColumnCount(8)
        self.client_table.setHorizontalHeaderLabels(["ID", "Username", "First Name", "Last Name", "Corporation", "Branch", "Created At", "Actions"])
        self.client_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.client_table.setAlternatingRowColors(True)
        self.client_table.setStyleSheet("""
            QTableWidget { background: white; gridline-color: #dee2e6; border: 1px solid #dee2e6; font-size: 11px; }
            QTableWidget::item { padding: 5px; }
            QHeaderView::section { background: #f8f9fa; padding: 8px; border: none; border-bottom: 2px solid #dee2e6; font-weight: bold; }
        """)
        header = self.client_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        table_layout.addWidget(self.client_table)
        layout.addWidget(table_frame)
        
        return widget

    # ========== LOAD METHODS ==========
    
    def _load_corp_dropdowns(self):
        """Load corporations into dropdowns"""
        try:
            rows = self.db.execute_query("SELECT id, name FROM corporations ORDER BY name")
            self.branch_corp_combo.clear()
            self.client_corp_combo.clear()
            # Preserve current filter selection
            current_filter = self.branch_filter_combo.currentData()
            self.branch_filter_combo.clear()
            self.branch_filter_combo.addItem("All Corporations", None)
            if rows:
                for r in rows:
                    self.branch_corp_combo.addItem(r['name'], r['id'])
                    self.client_corp_combo.addItem(r['name'], r['id'])
                    self.branch_filter_combo.addItem(r['name'], r['id'])
                # Restore filter selection if possible
                if current_filter:
                    idx = self.branch_filter_combo.findData(current_filter)
                    if idx >= 0:
                        self.branch_filter_combo.setCurrentIndex(idx)
        except Exception as e:
            print(f"Error loading corporations: {e}")

    def _on_tab_changed(self, index):
        """Refresh dropdowns when switching to branches or clients tab"""
        # Tab 0 = Corps, Tab 1 = Branches, Tab 2 = Clients, Tab 3 = Admin Users
        if index == 1:
            self._load_corp_dropdowns()
        elif index == 2:
            self._load_corp_dropdowns()
            self._refresh_client_branches()
        elif index == 3:
            self._load_admin_users()

    def _refresh_client_branches(self):
        """Refresh the branch dropdown in client form based on selected corporation"""
        corp_id = self.client_corp_combo.currentData()
        current_branch_id = self.client_branch_combo.currentData()
        self.client_branch_combo.clear()
        if corp_id:
            try:
                rows = self.db.execute_query("SELECT id, name FROM branches WHERE corporation_id = %s ORDER BY name", (corp_id,))
                if rows:
                    for r in rows:
                        self.client_branch_combo.addItem(r['name'], r['id'])
                    # Try to restore previous selection
                    if current_branch_id:
                        idx = self.client_branch_combo.findData(current_branch_id)
                        if idx >= 0:
                            self.client_branch_combo.setCurrentIndex(idx)
            except Exception as e:
                print(f"Error loading branches: {e}")

    def _on_client_corp_changed(self):
        """Update branch dropdown when corporation changes"""
        corp_id = self.client_corp_combo.currentData()
        self.client_branch_combo.clear()
        if corp_id:
            try:
                rows = self.db.execute_query("SELECT id, name FROM branches WHERE corporation_id = %s ORDER BY name", (corp_id,))
                if rows:
                    for r in rows:
                        self.client_branch_combo.addItem(r['name'], r['id'])
            except Exception as e:
                print(f"Error loading branches: {e}")

    def _load_corporations(self):
        """Load corporations with pagination"""
        try:
            # Get total count
            count_row = self.db.execute_query("SELECT COUNT(*) as cnt FROM corporations")
            self.corp_total = count_row[0]['cnt'] if count_row else 0
            
            total_pages = max(1, (self.corp_total + self.page_size - 1) // self.page_size)
            self.corp_page = min(self.corp_page, total_pages - 1)
            self.corp_page = max(0, self.corp_page)
            
            offset = self.corp_page * self.page_size
            rows = self.db.execute_query(
                "SELECT id, name, created_at FROM corporations ORDER BY name LIMIT %s OFFSET %s",
                (self.page_size, offset)
            )
            
            self.corp_table.setRowCount(0)
            if rows:
                for row_data in rows:
                    row_idx = self.corp_table.rowCount()
                    self.corp_table.insertRow(row_idx)
                    
                    self.corp_table.setItem(row_idx, 0, QTableWidgetItem(str(row_data['id'])))
                    self.corp_table.setItem(row_idx, 1, QTableWidgetItem(str(row_data['name'])))
                    self.corp_table.setItem(row_idx, 2, QTableWidgetItem(str(row_data.get('created_at', ''))[:19]))
                    
                    # Actions button
                    action_widget = QWidget()
                    action_layout = QHBoxLayout(action_widget)
                    action_layout.setContentsMargins(2, 2, 2, 2)
                    action_layout.setSpacing(2)
                    
                    del_btn = QPushButton("🗑️")
                    del_btn.setFixedSize(28, 24)
                    del_btn.setStyleSheet("QPushButton { background: #e74c3c; border: none; border-radius: 3px; } QPushButton:hover { background: #c0392b; }")
                    del_btn.clicked.connect(lambda checked, cid=row_data['id'], cname=row_data['name']: self._delete_corporation(cid, cname))
                    
                    action_layout.addWidget(del_btn)
                    self.corp_table.setCellWidget(row_idx, 3, action_widget)
            
            self.corp_page_label.setText(f"Page {self.corp_page + 1} of {total_pages} ({self.corp_total} total)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load corporations: {e}")

    def _on_branch_filter_changed(self):
        """Reset page and reload branches when filter changes"""
        self.branch_page = 0
        self._load_branches()

    def _load_branches(self):
        """Load branches with pagination and optional corporation filter"""
        try:
            corp_filter = self.branch_filter_combo.currentData()
            
            # Build count query
            if corp_filter:
                count_row = self.db.execute_query(
                    "SELECT COUNT(*) as cnt FROM branches WHERE corporation_id = %s", 
                    (corp_filter,)
                )
            else:
                count_row = self.db.execute_query("SELECT COUNT(*) as cnt FROM branches")
            
            self.branch_total = count_row[0]['cnt'] if count_row else 0
            
            total_pages = max(1, (self.branch_total + self.page_size - 1) // self.page_size)
            self.branch_page = min(self.branch_page, total_pages - 1)
            self.branch_page = max(0, self.branch_page)
            
            offset = self.branch_page * self.page_size
            
            # Build data query with optional filter
            if corp_filter:
                rows = self.db.execute_query("""
                    SELECT b.id, b.name, c.name as corp_name, b.created_at, b.is_registered,
                           COALESCE(b.os_name, '') as os_name
                    FROM branches b
                    LEFT JOIN corporations c ON b.corporation_id = c.id
                    WHERE b.corporation_id = %s
                    ORDER BY c.name, b.name
                    LIMIT %s OFFSET %s
                """, (corp_filter, self.page_size, offset))
            else:
                rows = self.db.execute_query("""
                    SELECT b.id, b.name, c.name as corp_name, b.created_at, b.is_registered,
                           COALESCE(b.os_name, '') as os_name
                    FROM branches b
                    LEFT JOIN corporations c ON b.corporation_id = c.id
                    ORDER BY c.name, b.name
                    LIMIT %s OFFSET %s
                """, (self.page_size, offset))
            
            self.branch_table.setRowCount(0)
            if rows:
                for row_data in rows:
                    row_idx = self.branch_table.rowCount()
                    self.branch_table.insertRow(row_idx)
                    
                    self.branch_table.setItem(row_idx, 0, QTableWidgetItem(str(row_data['id'])))
                    self.branch_table.setItem(row_idx, 1, QTableWidgetItem(str(row_data['name'])))
                    self.branch_table.setItem(row_idx, 2, QTableWidgetItem(str(row_data.get('corp_name', ''))))

                    # OS column (col 3) with inline edit button
                    os_val = row_data.get('os_name', '') or ''
                    os_widget = QWidget()
                    os_lay = QHBoxLayout(os_widget)
                    os_lay.setContentsMargins(2, 2, 2, 2)
                    os_lay.setSpacing(4)
                    os_label = QLabel(os_val if os_val else '—')
                    os_label.setStyleSheet("font-size:10px; color: #2c3e50;" if os_val else "font-size:10px; color: #aaa;")
                    os_edit_btn = QPushButton("✏️")
                    os_edit_btn.setFixedSize(24, 24)
                    os_edit_btn.setToolTip("Assign / change Operation Supervisor")
                    os_edit_btn.setStyleSheet("QPushButton { background: #3498db; border: none; border-radius: 3px; } QPushButton:hover { background: #2980b9; }")
                    os_edit_btn.clicked.connect(lambda checked, bid=row_data['id'], bname=row_data.get('name', ''), cur_os=os_val: self._edit_branch_os(bid, bname, cur_os))
                    os_lay.addWidget(os_label, 1)
                    os_lay.addWidget(os_edit_btn)
                    self.branch_table.setCellWidget(row_idx, 3, os_widget)

                    self.branch_table.setItem(row_idx, 4, QTableWidgetItem(str(row_data.get('created_at', ''))[:19]))
                    
                    # Registered toggle button with visible label + confirmation
                    is_registered = row_data.get('is_registered', 1)
                    reg_widget = QWidget()
                    reg_layout = QHBoxLayout(reg_widget)
                    reg_layout.setContentsMargins(2, 2, 2, 2)
                    reg_layout.setSpacing(6)

                    # Status label (explicit text so column isn't just an icon)
                    status_label = QLabel("Registered" if is_registered else "Not Registered")
                    status_label.setStyleSheet("font-size:10px;")
                    if is_registered:
                        status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size:10px;")
                    else:
                        status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size:10px;")

                    reg_btn = QPushButton("Toggle")
                    reg_btn.setFixedSize(60, 24)
                    if is_registered:
                        reg_btn.setStyleSheet("QPushButton { background: #27ae60; color: white; border: none; border-radius: 3px; font-size: 10px; } QPushButton:hover { background: #219a52; }")
                    else:
                        reg_btn.setStyleSheet("QPushButton { background: #e74c3c; color: white; border: none; border-radius: 3px; font-size: 10px; } QPushButton:hover { background: #c0392b; }")

                    # Pass branch name for confirmation message
                    reg_btn.clicked.connect(lambda checked, bid=row_data['id'], current=is_registered, bname=row_data.get('name', ''): self._toggle_branch_registered(bid, current, bname))

                    reg_layout.addWidget(status_label)
                    reg_layout.addWidget(reg_btn)
                    reg_layout.addStretch()
                    self.branch_table.setCellWidget(row_idx, 5, reg_widget)
                    
                    # Actions button
                    action_widget = QWidget()
                    action_layout = QHBoxLayout(action_widget)
                    action_layout.setContentsMargins(2, 2, 2, 2)
                    action_layout.setSpacing(2)
                    
                    del_btn = QPushButton("🗑️")
                    del_btn.setFixedSize(28, 24)
                    del_btn.setStyleSheet("QPushButton { background: #e74c3c; border: none; border-radius: 3px; } QPushButton:hover { background: #c0392b; }")
                    del_btn.clicked.connect(lambda checked, bid=row_data['id'], bname=row_data['name']: self._delete_branch(bid, bname))
                    
                    action_layout.addWidget(del_btn)
                    self.branch_table.setCellWidget(row_idx, 6, action_widget)
            
            self.branch_page_label.setText(f"Page {self.branch_page + 1} of {total_pages} ({self.branch_total} total)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load branches: {e}")

    def _edit_branch_os(self, branch_id, branch_name, current_os):
        """Open a dialog to assign / change the Operation Supervisor for a branch."""
        from PyQt5.QtWidgets import QInputDialog
        new_os, ok = QInputDialog.getText(
            self, "Assign Operation Supervisor",
            f"Enter OS name for branch '{branch_name}':",
            text=current_os or ""
        )
        if not ok:
            return
        new_os = new_os.strip()
        try:
            self.db.execute_query(
                "UPDATE branches SET os_name = %s WHERE id = %s",
                (new_os if new_os else None, branch_id)
            )
            QMessageBox.information(self, "Updated",
                f"OS for '{branch_name}' set to '{new_os}'." if new_os else f"OS for '{branch_name}' cleared.")
            self._load_branches()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update OS: {e}")

    def _toggle_branch_registered(self, branch_id, current_status, branch_name=None):
        """Toggle the registered status of a branch with confirmation"""
        new_status = 0 if current_status else 1
        status_text = "registered" if new_status else "not registered"

        # Ask for confirmation including branch name when available
        display_name = branch_name or str(branch_id)
        reply = QMessageBox.question(
            self, "Confirm Change",
            f"Are you sure you want to mark branch '{display_name}' as {status_text}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            result = self.db.execute_query(
                "UPDATE branches SET is_registered = %s WHERE id = %s",
                (new_status, branch_id)
            )
            if result is not None:
                QMessageBox.information(self, "Updated", f"Branch '{display_name}' marked as {status_text}.")
                self._load_branches()  # Refresh the table
            else:
                QMessageBox.critical(self, "Error", "Failed to update branch registration status.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update branch: {e}")

    def _load_clients(self):
        """Load clients with pagination and search"""
        try:
            search = self.client_search_input.text().strip()
            
            # Build query
            if search:
                count_query = "SELECT COUNT(*) as cnt FROM users WHERE role='user' AND (username LIKE %s OR first_name LIKE %s OR last_name LIKE %s)"
                search_param = f"%{search}%"
                count_row = self.db.execute_query(count_query, (search_param, search_param, search_param))
            else:
                count_row = self.db.execute_query("SELECT COUNT(*) as cnt FROM users WHERE role='user'")
            
            self.client_total = count_row[0]['cnt'] if count_row else 0
            
            total_pages = max(1, (self.client_total + self.page_size - 1) // self.page_size)
            self.client_page = min(self.client_page, total_pages - 1)
            self.client_page = max(0, self.client_page)
            
            offset = self.client_page * self.page_size
            
            if search:
                rows = self.db.execute_query("""
                    SELECT id, username, first_name, last_name, corporation, branch, created_at
                    FROM users WHERE role='user' AND (username LIKE %s OR first_name LIKE %s OR last_name LIKE %s)
                    ORDER BY id DESC LIMIT %s OFFSET %s
                """, (search_param, search_param, search_param, self.page_size, offset))
            else:
                rows = self.db.execute_query("""
                    SELECT id, username, first_name, last_name, corporation, branch, created_at
                    FROM users WHERE role='user'
                    ORDER BY id DESC LIMIT %s OFFSET %s
                """, (self.page_size, offset))
            
            self.client_table.setRowCount(0)
            if rows:
                for row_data in rows:
                    row_idx = self.client_table.rowCount()
                    self.client_table.insertRow(row_idx)
                    
                    self.client_table.setItem(row_idx, 0, QTableWidgetItem(str(row_data['id'])))
                    self.client_table.setItem(row_idx, 1, QTableWidgetItem(str(row_data.get('username', ''))))
                    self.client_table.setItem(row_idx, 2, QTableWidgetItem(str(row_data.get('first_name', ''))))
                    self.client_table.setItem(row_idx, 3, QTableWidgetItem(str(row_data.get('last_name', ''))))
                    self.client_table.setItem(row_idx, 4, QTableWidgetItem(str(row_data.get('corporation', ''))))
                    self.client_table.setItem(row_idx, 5, QTableWidgetItem(str(row_data.get('branch', ''))))
                    self.client_table.setItem(row_idx, 6, QTableWidgetItem(str(row_data.get('created_at', ''))[:19]))
                    
                    # Actions buttons
                    action_widget = QWidget()
                    action_layout = QHBoxLayout(action_widget)
                    action_layout.setContentsMargins(2, 2, 2, 2)
                    action_layout.setSpacing(2)
                    
                    edit_btn = QPushButton("✏️")
                    edit_btn.setFixedSize(28, 24)
                    edit_btn.setStyleSheet("QPushButton { background: #3498db; border: none; border-radius: 3px; } QPushButton:hover { background: #2980b9; }")
                    edit_btn.clicked.connect(lambda checked, cdata=row_data: self._edit_client(cdata))
                    
                    del_btn = QPushButton("🗑️")
                    del_btn.setFixedSize(28, 24)
                    del_btn.setStyleSheet("QPushButton { background: #e74c3c; border: none; border-radius: 3px; } QPushButton:hover { background: #c0392b; }")
                    del_btn.clicked.connect(lambda checked, cid=row_data['id'], cname=row_data.get('username', ''): self._delete_client(cid, cname))
                    
                    action_layout.addWidget(edit_btn)
                    action_layout.addWidget(del_btn)
                    self.client_table.setCellWidget(row_idx, 7, action_widget)
            
            self.client_page_label.setText(f"Page {self.client_page + 1} of {total_pages} ({self.client_total} total)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load clients: {e}")

    # ========== PAGINATION ==========
    
    def _change_corp_page(self, delta):
        self.corp_page += delta
        self._load_corporations()

    def _change_branch_page(self, delta):
        self.branch_page += delta
        self._load_branches()

    def _change_client_page(self, delta):
        self.client_page += delta
        self._load_clients()

    # ========== ADD METHODS ==========
    
    def _add_corporation(self):
        name = self.corp_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Required", "Please enter a corporation name.")
            return
        try:
            cid = create_corporation(name)
            if cid:
                QMessageBox.information(self, "✅ Created", f"Corporation '{name}' created (ID: {cid})")
                self.corp_name_input.clear()
                self._load_corporations()
                self._load_corp_dropdowns()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create corporation: {e}")

    def _add_branch(self):
        name = self.branch_name_input.text().strip()
        corp_id = self.branch_corp_combo.currentData()
        os_name = self.branch_os_input.text().strip() or None
        if not corp_id:
            QMessageBox.warning(self, "Selection Required", "Please select a corporation.")
            return
        if not name:
            QMessageBox.warning(self, "Input Required", "Please enter a branch name.")
            return
        try:
            bid = create_branch(name, corp_id)
            if bid:
                # Save OS name if provided
                if os_name:
                    self.db.execute_query(
                        "UPDATE branches SET os_name = %s WHERE id = %s",
                        (os_name, bid)
                    )
                QMessageBox.information(self, "✅ Created", f"Branch '{name}' created (ID: {bid})")
                self.branch_name_input.clear()
                self.branch_os_input.clear()
                self._load_branches()
                # Refresh branch dropdown in clients tab so new branch appears
                self._refresh_client_branches()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create branch: {e}")

    def _add_client(self):
        first = self.client_first_input.text().strip()
        last = self.client_last_input.text().strip()
        corp_id = self.client_corp_combo.currentData()
        branch_id = self.client_branch_combo.currentData()
        password = self.client_password_input.text() or None

        if not (first and last):
            QMessageBox.warning(self, "Input Required", "Please enter first and last names.")
            return
        if not corp_id or not branch_id:
            QMessageBox.warning(self, "Selection Required", "Please select corporation and branch.")
            return

        try:
            row = create_client(first, last, corp_id, branch_id, password)
            if row:
                QMessageBox.information(self, "✅ Created", f"Client created!\nUsername: {row['username']}\nID: {row['id']}")
                self.client_first_input.clear()
                self.client_last_input.clear()
                self.client_password_input.clear()
                self._load_clients()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create client: {e}")

    # ========== EDIT METHODS ==========
    
    def _edit_client(self, client_data):
        """Open edit dialog for client"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Client: {client_data.get('username', '')}")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        layout.setSpacing(10)
        
        # Fields
        username_label = QLabel(client_data.get('username', ''))
        username_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        
        first_input = QLineEdit(client_data.get('first_name', ''))
        last_input = QLineEdit(client_data.get('last_name', ''))
        
        corp_combo = QComboBox()
        branch_combo = QComboBox()
        
        # Load corporations
        try:
            corps = self.db.execute_query("SELECT id, name FROM corporations ORDER BY name")
            if corps:
                for c in corps:
                    corp_combo.addItem(c['name'], c['id'])
                    if c['name'] == client_data.get('corporation'):
                        corp_combo.setCurrentIndex(corp_combo.count() - 1)
        except:
            pass

        # Load branches based on current corporation
        def load_branches_for_edit():
            corp_id = corp_combo.currentData()
            branch_combo.clear()
            if corp_id:
                try:
                    branches = self.db.execute_query("SELECT id, name FROM branches WHERE corporation_id = %s ORDER BY name", (corp_id,))
                    if branches:
                        for b in branches:
                            branch_combo.addItem(b['name'], b['id'])
                            if b['name'] == client_data.get('branch'):
                                branch_combo.setCurrentIndex(branch_combo.count() - 1)
                except:
                    pass
        
        corp_combo.currentIndexChanged.connect(load_branches_for_edit)
        load_branches_for_edit()
        
        password_input = QLineEdit()
        password_input.setPlaceholderText("Leave empty to keep current")
        password_input.setEchoMode(QLineEdit.Password)
        
        layout.addRow("Username:", username_label)
        layout.addRow("First Name:", first_input)
        layout.addRow("Last Name:", last_input)
        layout.addRow("Corporation:", corp_combo)
        layout.addRow("Branch:", branch_combo)
        layout.addRow("New Password:", password_input)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                # Update query
                update_fields = []
                update_values = []
                
                new_first = first_input.text().strip()
                new_last = last_input.text().strip()
                new_corp = corp_combo.currentText()
                new_branch = branch_combo.currentText()
                new_password = password_input.text()
                
                if new_first:
                    update_fields.append("first_name = %s")
                    update_values.append(new_first)
                if new_last:
                    update_fields.append("last_name = %s")
                    update_values.append(new_last)
                if new_corp:
                    update_fields.append("corporation = %s")
                    update_values.append(new_corp)
                if new_branch:
                    update_fields.append("branch = %s")
                    update_values.append(new_branch)
                if new_password:
                    # Hash the new password before storing
                    hashed = hash_password(new_password)
                    update_fields.append("password = %s")
                    update_values.append(hashed)
                
                if update_fields:
                    update_values.append(client_data['id'])
                    query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                    self.db.execute_query(query, tuple(update_values))
                    QMessageBox.information(self, "✅ Updated", "Client updated successfully!")
                    self._load_clients()
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update client: {e}")

    # ========== DELETE METHODS ==========
    
    def _delete_corporation(self, corp_id, corp_name):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete corporation '{corp_name}'?\n\nThis may affect related branches and entries.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.db.execute_query("DELETE FROM corporations WHERE id = %s", (corp_id,))
                QMessageBox.information(self, "✅ Deleted", f"Corporation '{corp_name}' deleted.")
                self._load_corporations()
                self._load_corp_dropdowns()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    def _delete_branch(self, branch_id, branch_name):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete branch '{branch_name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.db.execute_query("DELETE FROM branches WHERE id = %s", (branch_id,))
                QMessageBox.information(self, "✅ Deleted", f"Branch '{branch_name}' deleted.")
                self._load_branches()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    # ========== ADMIN USERS TAB ==========

    def _build_admin_users_tab(self):
        """Build Admin / Super Admin user management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # ── Description banner ───────────────────────────────────────────────
        info = QLabel(
            "👑  Manage Admin and Super Admin accounts.  "
            "Super Admins can add/remove cash-flow fields for any brand."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "background:#fef9e7; border:1px solid #f1c40f; border-radius:5px;"
            "padding:8px; color:#7d6608; font-size:11px;"
        )
        layout.addWidget(info)

        # ── Add form ──────────────────────────────────────────────────────────
        form_frame = QFrame()
        form_frame.setStyleSheet(
            "QFrame { background:#f8f9fa; border-radius:6px; padding:10px; }"
        )
        form_layout = QHBoxLayout(form_frame)
        form_layout.setSpacing(10)

        self.admin_username_input = QLineEdit()
        self.admin_username_input.setPlaceholderText("Username")
        self.admin_username_input.setMinimumWidth(140)

        self.admin_password_input = QLineEdit()
        self.admin_password_input.setPlaceholderText("Password")
        self.admin_password_input.setEchoMode(QLineEdit.Password)
        self.admin_password_input.setMinimumWidth(140)

        self.admin_role_combo = QComboBox()
        self.admin_role_combo.addItem("admin",       "admin")
        self.admin_role_combo.addItem("super_admin", "super_admin")
        self.admin_role_combo.setMinimumWidth(130)
        self.admin_role_combo.setStyleSheet(
            "QComboBox { font-weight:bold; } "
        )
        self.admin_role_combo.currentIndexChanged.connect(self._on_admin_role_changed)

        # Brand (account_type) dropdown - only relevant for admin role
        self.admin_brand_label = QLabel("Brand:")
        self.admin_brand_combo = QComboBox()
        self.admin_brand_combo.addItem("Brand A", 1)
        self.admin_brand_combo.addItem("Brand B", 2)
        self.admin_brand_combo.setMinimumWidth(100)
        self.admin_brand_combo.setStyleSheet("QComboBox { font-weight:bold; }")

        add_admin_btn = QPushButton("➕ Add User")
        add_admin_btn.setStyleSheet(
            "QPushButton { background:#8e44ad; color:white; padding:6px 16px;"
            " border:none; border-radius:4px; font-weight:bold; }"
            "QPushButton:hover { background:#7d3c98; }"
        )
        add_admin_btn.clicked.connect(self._add_admin_user)

        form_layout.addWidget(QLabel("Username:"))
        form_layout.addWidget(self.admin_username_input)
        form_layout.addWidget(QLabel("Password:"))
        form_layout.addWidget(self.admin_password_input)
        form_layout.addWidget(QLabel("Role:"))
        form_layout.addWidget(self.admin_role_combo)
        form_layout.addWidget(self.admin_brand_label)
        form_layout.addWidget(self.admin_brand_combo)
        form_layout.addWidget(add_admin_btn)
        form_layout.addStretch()
        layout.addWidget(form_frame)

        # ── Table ─────────────────────────────────────────────────────────────
        ctrl_bar = QHBoxLayout()
        show_btn = QPushButton("📋 Show Admin Users")
        show_btn.setStyleSheet(
            "QPushButton { background:#3498db; color:white; padding:6px 16px;"
            " border:none; border-radius:4px; font-weight:bold; }"
            "QPushButton:hover { background:#2980b9; }"
        )
        show_btn.clicked.connect(self._load_admin_users)
        ctrl_bar.addWidget(show_btn)
        ctrl_bar.addStretch()
        layout.addLayout(ctrl_bar)

        self.admin_table = QTableWidget()
        self.admin_table.setColumnCount(5)
        self.admin_table.setHorizontalHeaderLabels(
            ["ID", "Username", "Role", "Brand", "Actions"]
        )
        self.admin_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.admin_table.setAlternatingRowColors(True)
        self.admin_table.setStyleSheet("""
            QTableWidget { background:white; gridline-color:#dee2e6;
                border:1px solid #dee2e6; font-size:11px; }
            QTableWidget::item { padding:5px; }
            QHeaderView::section { background:#f8f9fa; padding:8px;
                border:none; border-bottom:2px solid #dee2e6;
                font-weight:bold; }
        """)
        hdr = self.admin_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        layout.addWidget(self.admin_table)

        return widget

    def _load_admin_users(self):
        """Load all admin and super_admin users into the table."""
        try:
            rows = self.db.execute_query(
                "SELECT id, username, role, account_type, created_at "
                "FROM users WHERE role IN ('admin','super_admin') "
                "ORDER BY role DESC, username"
            )
            self.admin_table.setRowCount(0)
            if not rows:
                return
            for row_data in rows:
                ri = self.admin_table.rowCount()
                self.admin_table.insertRow(ri)

                self.admin_table.setItem(ri, 0, QTableWidgetItem(str(row_data['id'])))
                self.admin_table.setItem(ri, 1, QTableWidgetItem(str(row_data.get('username', ''))))

                role = str(row_data.get('role', ''))
                role_item = QTableWidgetItem(role)
                if role == 'super_admin':
                    role_item.setForeground(__import__('PyQt5.QtGui', fromlist=['QColor']).QColor('#8e44ad'))
                    role_item.setFont(__import__('PyQt5.QtGui', fromlist=['QFont']).QFont('', -1, 75))  # bold
                self.admin_table.setItem(ri, 2, role_item)

                # Brand column
                acct_type = row_data.get('account_type', 2)
                brand_text = "Brand A" if acct_type == 1 else "Brand B"
                brand_item = QTableWidgetItem(brand_text)
                if role == 'super_admin':
                    brand_item.setText("All")  # Super admin sees all
                self.admin_table.setItem(ri, 3, brand_item)

                # Actions
                act_w = QWidget()
                act_l = QHBoxLayout(act_w)
                act_l.setContentsMargins(2, 2, 2, 2)
                act_l.setSpacing(4)

                reset_btn = QPushButton("🔑 Reset PW")
                reset_btn.setFixedHeight(24)
                reset_btn.setStyleSheet(
                    "QPushButton { background:#f39c12; color:white; border:none;"
                    " border-radius:3px; font-size:10px; padding:0 8px; }"
                    "QPushButton:hover { background:#d68910; }"
                )
                reset_btn.clicked.connect(
                    lambda _, uid=row_data['id'], uname=row_data.get('username', ''):
                    self._reset_admin_password(uid, uname)
                )

                # Edit Brand button (only for admin, not super_admin)
                if role == 'admin':
                    edit_brand_btn = QPushButton("🏷️ Brand")
                    edit_brand_btn.setFixedHeight(24)
                    edit_brand_btn.setStyleSheet(
                        "QPushButton { background:#3498db; color:white; border:none;"
                        " border-radius:3px; font-size:10px; padding:0 8px; }"
                        "QPushButton:hover { background:#2980b9; }"
                    )
                    edit_brand_btn.clicked.connect(
                        lambda _, uid=row_data['id'], uname=row_data.get('username', ''), at=acct_type:
                        self._edit_admin_brand(uid, uname, at)
                    )
                    act_l.addWidget(edit_brand_btn)

                del_btn = QPushButton("🗑️")
                del_btn.setFixedSize(28, 24)
                del_btn.setStyleSheet(
                    "QPushButton { background:#e74c3c; border:none; border-radius:3px; }"
                    "QPushButton:hover { background:#c0392b; }"
                )
                del_btn.clicked.connect(
                    lambda _, uid=row_data['id'], uname=row_data.get('username', ''):
                    self._delete_admin_user(uid, uname)
                )

                act_l.addWidget(reset_btn)
                act_l.addWidget(del_btn)
                self.admin_table.setCellWidget(ri, 4, act_w)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load admin users: {e}")

    def _add_admin_user(self):
        """Insert a new admin or super_admin user."""
        username = self.admin_username_input.text().strip()
        password = self.admin_password_input.text()
        role = self.admin_role_combo.currentData()
        account_type = self.admin_brand_combo.currentData() if role == 'admin' else 2

        if not username:
            QMessageBox.warning(self, "Input Required", "Please enter a username.")
            return
        if not password:
            QMessageBox.warning(self, "Input Required", "Please enter a password.")
            return

        try:
            # Check for duplicate username
            existing = self.db.execute_query(
                "SELECT id FROM users WHERE username = %s", (username,)
            )
            if existing:
                QMessageBox.warning(
                    self, "Duplicate",
                    f"A user named '{username}' already exists."
                )
                return

            hashed = hash_password(password)
            self.db.execute_query(
                "INSERT INTO users (username, password, role, branch, corporation, account_type) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (username, hashed, role, "", "", account_type)
            )
            label = "Super Admin" if role == "super_admin" else "Admin"
            brand_info = f" ({self.admin_brand_combo.currentText()})" if role == 'admin' else ""
            QMessageBox.information(
                self, "✅ Created",
                f"{label} user '{username}'{brand_info} created successfully!"
            )
            self.admin_username_input.clear()
            self.admin_password_input.clear()
            self._load_admin_users()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create user: {e}")

    def _on_admin_role_changed(self, index):
        """Show/hide brand dropdown based on role selection."""
        role = self.admin_role_combo.currentData()
        is_admin = (role == 'admin')
        self.admin_brand_label.setVisible(is_admin)
        self.admin_brand_combo.setVisible(is_admin)

    def _edit_admin_brand(self, user_id: int, username: str, current_type: int):
        """Dialog to change an admin's brand/account_type."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Brand – {username}")
        dialog.setFixedWidth(280)
        form = QFormLayout(dialog)
        form.setSpacing(10)
        form.setContentsMargins(16, 16, 16, 16)

        brand_combo = QComboBox()
        brand_combo.addItem("Brand A", 1)
        brand_combo.addItem("Brand B", 2)
        # Set current selection
        brand_combo.setCurrentIndex(0 if current_type == 1 else 1)

        form.addRow("Brand:", brand_combo)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        form.addRow(btns)

        if dialog.exec_() == QDialog.Accepted:
            new_type = brand_combo.currentData()
            if new_type == current_type:
                return  # No change
            try:
                self.db.execute_query(
                    "UPDATE users SET account_type = %s WHERE id = %s",
                    (new_type, user_id)
                )
                brand_name = "Brand A" if new_type == 1 else "Brand B"
                QMessageBox.information(
                    self, "✅ Updated",
                    f"'{username}' is now assigned to {brand_name}."
                )
                self._load_admin_users()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update brand: {e}")

    def _delete_admin_user(self, user_id: int, username: str):
        """Delete an admin / super_admin account."""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete admin user '{username}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.db.execute_query(
                    "DELETE FROM users WHERE id = %s AND role IN ('admin','super_admin')",
                    (user_id,)
                )
                QMessageBox.information(self, "✅ Deleted", f"User '{username}' deleted.")
                self._load_admin_users()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete user: {e}")

    def _reset_admin_password(self, user_id: int, username: str):
        """Open a small dialog to reset an admin user's password."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Reset Password – {username}")
        dialog.setFixedWidth(320)
        form = QFormLayout(dialog)
        form.setSpacing(10)
        form.setContentsMargins(16, 16, 16, 16)

        new_pw = QLineEdit()
        new_pw.setPlaceholderText("New password")
        new_pw.setEchoMode(QLineEdit.Password)
        confirm_pw = QLineEdit()
        confirm_pw.setPlaceholderText("Confirm password")
        confirm_pw.setEchoMode(QLineEdit.Password)

        form.addRow("New Password:", new_pw)
        form.addRow("Confirm:", confirm_pw)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        form.addRow(btns)

        if dialog.exec_() == QDialog.Accepted:
            p1 = new_pw.text()
            p2 = confirm_pw.text()
            if not p1:
                QMessageBox.warning(self, "Empty", "Password cannot be empty.")
                return
            if p1 != p2:
                QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
                return
            try:
                hashed = hash_password(p1)
                self.db.execute_query(
                    "UPDATE users SET password = %s WHERE id = %s",
                    (hashed, user_id)
                )
                QMessageBox.information(
                    self, "✅ Updated",
                    f"Password for '{username}' has been reset."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to reset password: {e}")

    def _delete_client(self, client_id, username):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete client '{username}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.db.execute_query("DELETE FROM users WHERE id = %s", (client_id,))
                QMessageBox.information(self, "✅ Deleted", f"Client '{username}' deleted.")
                self._load_clients()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")
