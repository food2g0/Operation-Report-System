"""
User Management Page for Admin Dashboard
Manages corporations, branches, and client accounts with pagination
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QMessageBox, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QDialogButtonBox,
    QSpinBox, QTabWidget, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from db_connect_pooled import db_manager
from admin_manage import (create_corporation, create_branch, create_client,
                         get_all_supervisors, create_supervisor, delete_supervisor,
                         update_supervisor)
from security import hash_password


class UserManagementPage(QWidget):
    """Page for managing corporations, branches, and client accounts"""
    
    def __init__(self, is_super_admin=False):
        super().__init__()
        self.db = db_manager
        self.is_super_admin = is_super_admin
        
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
            QTabBar::tab { background: #f8f9fa; color: #2c3e50; padding: 8px 20px; margin-right: 2px; border: 1px solid #dee2e6; border-bottom: none; border-radius: 4px 4px 0 0; }
            QTabBar::tab:selected { background: white; color: #2c3e50; font-weight: bold; }
            QTabBar::tab:hover { background: #e9ecef; }
        """)
        
        # Create tabs
        self.tabs.addTab(self._build_corporations_tab(), "📊 Corporations")
        self.tabs.addTab(self._build_branches_tab(), "🏢 Branches")
        self.tabs.addTab(self._build_clients_tab(), "👥 Clients")
        
        # Admin Users and Operation Supervisors tabs only visible to super admins
        if self.is_super_admin:
            self.tabs.addTab(self._build_admin_users_tab(), "Admin Users")
            self.tabs.addTab(self._build_os_tab(), "📋 Operation Supervisors")
        
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
        form_main_layout = QVBoxLayout(form_frame)
        
        row1_layout = QHBoxLayout()
        
        self.branch_corp_combo = QComboBox()
        self.branch_corp_combo.setMinimumWidth(150)
        
        self.branch_corp_combo2 = QComboBox()
        self.branch_corp_combo2.setMinimumWidth(150)
        self.branch_corp_combo2.addItem("-- None --", None)
        
        self.branch_name_input = QLineEdit()
        self.branch_name_input.setPlaceholderText("Enter branch name")
        self.branch_name_input.setMinimumWidth(200)

        self.branch_os_combo = QComboBox()
        self.branch_os_combo.setMinimumWidth(180)
        self._load_os_dropdown()
        
        row1_layout.addWidget(QLabel("Corporation:"))
        row1_layout.addWidget(self.branch_corp_combo)
        row1_layout.addWidget(QLabel("Sub Corporation (optional):"))
        row1_layout.addWidget(self.branch_corp_combo2)
        row1_layout.addWidget(QLabel("Branch Name:"))
        row1_layout.addWidget(self.branch_name_input)
        row1_layout.addWidget(QLabel("Group:"))
        row1_layout.addWidget(self.branch_os_combo)
        row1_layout.addStretch()
        

        row2_layout = QHBoxLayout()
        
        self.branch_area_input = QLineEdit()
        self.branch_area_input.setPlaceholderText("Area")
        self.branch_area_input.setMinimumWidth(120)
        
        self.branch_global_combo = QComboBox()
        self.branch_global_combo.addItem("-- Global --", None)
        self.branch_global_combo.addItem("GLOBAL", "GLOBAL")
        self.branch_global_combo.addItem("NO GLOBAL", "NO GLOBAL")
        self.branch_global_combo.setMinimumWidth(100)
        
        self.branch_sunday_combo = QComboBox()
        self.branch_sunday_combo.addItem("-- Sunday --", None)
        self.branch_sunday_combo.addItem("YES", "YES")
        self.branch_sunday_combo.addItem("NO", "NO")
        self.branch_sunday_combo.setMinimumWidth(100)
        
        self.branch_lob_combo = QComboBox()
        self.branch_lob_combo.addItem("-- Line of Business --", None)
        self.branch_lob_combo.addItem("GROUP 1", "GROUP 1")
        self.branch_lob_combo.addItem("GROUP 2", "GROUP 2")
        self.branch_lob_combo.addItem("GROUP 3", "GROUP 3")
        self.branch_lob_combo.setMinimumWidth(130)
        
        add_btn = QPushButton("➕ Add")
        add_btn.setStyleSheet("QPushButton { background: #27ae60; color: white; padding: 6px 16px; border: none; border-radius: 4px; font-weight: bold; } QPushButton:hover { background: #219a52; }")
        add_btn.clicked.connect(self._add_branch)
        
        row2_layout.addWidget(QLabel("Area:"))
        row2_layout.addWidget(self.branch_area_input)
        row2_layout.addWidget(QLabel("Global:"))
        row2_layout.addWidget(self.branch_global_combo)
        row2_layout.addWidget(QLabel("Sunday:"))
        row2_layout.addWidget(self.branch_sunday_combo)
        row2_layout.addWidget(QLabel("LOB:"))
        row2_layout.addWidget(self.branch_lob_combo)
        row2_layout.addWidget(add_btn)
        row2_layout.addStretch()
        
        form_main_layout.addLayout(row1_layout)
        form_main_layout.addLayout(row2_layout)
        
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
        control_bar.addSpacing(10)
        
        self.branch_search_input = QLineEdit()
        self.branch_search_input.setPlaceholderText("Search branch name...")
        self.branch_search_input.setMinimumWidth(150)
        self.branch_search_input.setClearButtonEnabled(True)
        self.branch_search_input.returnPressed.connect(self._on_branch_filter_changed)
        control_bar.addWidget(QLabel("Search:"))
        control_bar.addWidget(self.branch_search_input)
        
        control_bar.addStretch()
        control_bar.addWidget(prev_btn)
        control_bar.addWidget(self.branch_page_label)
        control_bar.addWidget(next_btn)
        
        table_layout.addLayout(control_bar)
        
        # Table
        self.branch_table = QTableWidget()
        self.branch_table.setColumnCount(12)
        self.branch_table.setHorizontalHeaderLabels(["ID", "Branch Name", "Corporation", "Sub Corporation", "OS", "Area", "Global", "Sunday", "LOB", "Created At", "Registered", "Actions"])
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
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(11, QHeaderView.ResizeToContents)
        
        table_layout.addWidget(self.branch_table)
        layout.addWidget(table_frame)
        
        return widget

    def _build_clients_tab(self):

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background: #f8f9fa; border-radius: 6px; padding: 10px; }")
        form_layout = QVBoxLayout(form_frame)
        
        row1 = QHBoxLayout()
        self.client_corp_combo = QComboBox()
        self.client_corp_combo.setMinimumWidth(150)
        self.client_corp_combo.currentIndexChanged.connect(self._on_client_corp_changed)
        self.client_branch_combo = QComboBox()
        self.client_branch_combo.setMinimumWidth(150)
        
        row1.addWidget(QLabel("Corp:"))
        row1.addWidget(self.client_corp_combo)
        row1.addWidget(QLabel("Branch:"))
        row1.addWidget(self.client_branch_combo)
        
        row2 = QHBoxLayout()
        self.client_password_input = QLineEdit()
        self.client_password_input.setPlaceholderText("Password")
        self.client_password_input.setEchoMode(QLineEdit.Password)
        self.client_password_input.setMinimumWidth(150)
        
        client_show_pw = QCheckBox("Show")
        client_show_pw.toggled.connect(lambda checked: self.client_password_input.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password))
        
        add_btn = QPushButton("➕ Add Client")
        add_btn.setStyleSheet("QPushButton { background: #27ae60; color: white; padding: 6px 16px; border: none; border-radius: 4px; font-weight: bold; } QPushButton:hover { background: #219a52; }")
        add_btn.clicked.connect(self._add_client)
        
        row2.addWidget(QLabel("Password:"))
        row2.addWidget(self.client_password_input)
        row2.addWidget(client_show_pw)
        row2.addWidget(add_btn)
        row2.addStretch()
        
        form_layout.addLayout(row1)
        form_layout.addLayout(row2)
        layout.addWidget(form_frame)

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
        self.client_search_input.setPlaceholderText("Search by username or branch...")
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
        self.client_table.setColumnCount(6)
        self.client_table.setHorizontalHeaderLabels(["ID", "Username", "Corporation", "Branch", "Created At", "Actions"])
        self.client_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.client_table.setAlternatingRowColors(True)
        self.client_table.setStyleSheet("""
            QTableWidget { background: white; gridline-color: #dee2e6; border: 1px solid #dee2e6; font-size: 11px; }
            QTableWidget::item { padding: 5px; }
            QHeaderView::section { background: #f8f9fa; padding: 8px; border: none; border-bottom: 2px solid #dee2e6; font-weight: bold; }
        """)
        header = self.client_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        table_layout.addWidget(self.client_table)
        layout.addWidget(table_frame)
        
        return widget

    
    def _load_corp_dropdowns(self):
        """Load corporations into dropdowns"""
        try:
            rows = self.db.execute_query("SELECT id, name FROM corporations ORDER BY name")
            self.branch_corp_combo.clear()
            self.branch_corp_combo2.clear()
            self.branch_corp_combo2.addItem("-- None --", None)
            self.client_corp_combo.clear()
            # Preserve current filter selection
            current_filter = self.branch_filter_combo.currentData()
            self.branch_filter_combo.clear()
            self.branch_filter_combo.addItem("All Corporations", None)
            if rows:
                for r in rows:
                    self.branch_corp_combo.addItem(r['name'], r['id'])
                    self.branch_corp_combo2.addItem(r['name'], r['id'])
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


        if index == 1:
            self._load_corp_dropdowns()
            self._load_os_dropdown()
        elif index == 2:
            self._load_corp_dropdowns()
            self._refresh_client_branches()
        elif index == 3 and self.is_super_admin:
            self._load_admin_users()
        elif index == 4 and self.is_super_admin:
            self._refresh_os_list()

    def _refresh_client_branches(self):
        """Refresh the branch dropdown in client form based on selected corporation"""
        corp_id = self.client_corp_combo.currentData()
        current_branch_id = self.client_branch_combo.currentData()
        self.client_branch_combo.clear()
        if corp_id:
            try:
                rows = self.db.execute_query("SELECT id, name FROM branches WHERE corporation_id = %s OR sub_corporation_id = %s ORDER BY name", (corp_id, corp_id))
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
                rows = self.db.execute_query("SELECT id, name FROM branches WHERE corporation_id = %s OR sub_corporation_id = %s ORDER BY name", (corp_id, corp_id))
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
        """Load branches with pagination and optional corporation/name filter"""
        try:
            corp_filter = self.branch_filter_combo.currentData()
            search_text = self.branch_search_input.text().strip()
            
            # Build WHERE conditions
            conditions = []
            params = []
            if corp_filter:
                # Filter by either main corporation OR sub corporation
                conditions.append("(b.corporation_id = %s OR b.sub_corporation_id = %s)")
                params.append(corp_filter)
                params.append(corp_filter)
            if search_text:
                conditions.append("b.name LIKE %s")
                params.append(f"%{search_text}%")
            
            where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
            
            # Count query
            count_row = self.db.execute_query(
                f"SELECT COUNT(*) as cnt FROM branches b {where_clause}",
                tuple(params) if params else None
            )
            
            self.branch_total = count_row[0]['cnt'] if count_row else 0
            
            total_pages = max(1, (self.branch_total + self.page_size - 1) // self.page_size)
            self.branch_page = min(self.branch_page, total_pages - 1)
            self.branch_page = max(0, self.branch_page)
            
            offset = self.branch_page * self.page_size
            
            # Build data query with filters
            data_params = list(params) + [self.page_size, offset]
            rows = self.db.execute_query(f"""
                SELECT b.id, b.name, c.name as corp_name, b.created_at, b.is_registered,
                       COALESCE(b.os_name, '') as os_name,
                       COALESCE(b.area, '') as area,
                       COALESCE(b.global_tag, '') as global_tag,
                       COALESCE(b.sunday, '') as sunday,
                       COALESCE(b.line_of_business, '') as line_of_business,
                       b.sub_corporation_id,
                       COALESCE(sc.name, '') as sub_corp_name
                FROM branches b
                LEFT JOIN corporations c ON b.corporation_id = c.id
                LEFT JOIN corporations sc ON b.sub_corporation_id = sc.id
                {where_clause}
                ORDER BY c.name, b.name
                LIMIT %s OFFSET %s
            """, tuple(data_params))
            
            self.branch_table.setRowCount(0)
            if rows:
                for row_data in rows:
                    row_idx = self.branch_table.rowCount()
                    self.branch_table.insertRow(row_idx)
                    
                    self.branch_table.setItem(row_idx, 0, QTableWidgetItem(str(row_data['id'])))
                    self.branch_table.setItem(row_idx, 1, QTableWidgetItem(str(row_data['name'])))
                    
                    corp_name = str(row_data.get('corp_name', '')) or ''
                    sub_corp_name = str(row_data.get('sub_corp_name', '')) or ''
                    
                    corp_widget = QWidget()
                    corp_lay = QHBoxLayout(corp_widget)
                    corp_lay.setContentsMargins(2, 2, 2, 2)
                    corp_lay.setSpacing(4)
                    
                    corp_label = QLabel(corp_name if corp_name else '—')
                    corp_label.setStyleSheet("font-size:10px; color: #2c3e50;" if corp_name else "font-size:10px; color: #aaa;")
                    
                    corp_edit_btn = QPushButton("✏️")
                    corp_edit_btn.setFixedSize(24, 24)
                    corp_edit_btn.setToolTip("Edit Main/Sub Corporation")
                    corp_edit_btn.setStyleSheet("QPushButton { background: #3498db; border: none; border-radius: 3px; } QPushButton:hover { background: #2980b9; }")
                    corp_edit_btn.clicked.connect(lambda checked, bid=row_data['id'], bname=row_data.get('name', ''), mcorp=row_data.get('corporation_id'), scorp=row_data.get('sub_corporation_id'): self._edit_branch_corporations(bid, bname, mcorp, scorp))
                    
                    corp_lay.addWidget(corp_label, 1)
                    corp_lay.addWidget(corp_edit_btn)
                    self.branch_table.setCellWidget(row_idx, 2, corp_widget)
                    
                    sub_corp_label = QLabel(sub_corp_name if sub_corp_name else '—')
                    sub_corp_label.setStyleSheet("font-size:10px; color: #2c3e50;" if sub_corp_name else "font-size:10px; color: #aaa;")
                    self.branch_table.setItem(row_idx, 3, QTableWidgetItem(sub_corp_label.text()))

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
                    self.branch_table.setCellWidget(row_idx, 4, os_widget)

                    area_val = row_data.get('area', '') or ''
                    area_widget = QWidget()
                    area_lay = QHBoxLayout(area_widget)
                    area_lay.setContentsMargins(2, 2, 2, 2)
                    area_lay.setSpacing(4)
                    area_label = QLabel(area_val if area_val else '—')
                    area_label.setStyleSheet("font-size:10px; color: #2c3e50;" if area_val else "font-size:10px; color: #aaa;")
                    area_edit_btn = QPushButton("✏️")
                    area_edit_btn.setFixedSize(24, 24)
                    area_edit_btn.setToolTip("Edit Area")
                    area_edit_btn.setStyleSheet("QPushButton { background: #3498db; border: none; border-radius: 3px; } QPushButton:hover { background: #2980b9; }")
                    area_edit_btn.clicked.connect(lambda checked, bid=row_data['id'], bname=row_data.get('name', ''), cur=area_val: self._edit_branch_field(bid, bname, 'area', 'Area', cur))
                    area_lay.addWidget(area_label, 1)
                    area_lay.addWidget(area_edit_btn)
                    self.branch_table.setCellWidget(row_idx, 5, area_widget)

                    global_val = row_data.get('global_tag', '') or ''
                    global_widget = QWidget()
                    global_lay = QHBoxLayout(global_widget)
                    global_lay.setContentsMargins(2, 2, 2, 2)
                    global_lay.setSpacing(4)
                    global_label = QLabel(global_val if global_val else '—')
                    global_label.setStyleSheet("font-size:10px; color: #2c3e50;" if global_val else "font-size:10px; color: #aaa;")
                    global_edit_btn = QPushButton("✏️")
                    global_edit_btn.setFixedSize(24, 24)
                    global_edit_btn.setToolTip("Edit Global")
                    global_edit_btn.setStyleSheet("QPushButton { background: #3498db; border: none; border-radius: 3px; } QPushButton:hover { background: #2980b9; }")
                    global_edit_btn.clicked.connect(lambda checked, bid=row_data['id'], bname=row_data.get('name', ''), cur=global_val: self._edit_branch_dropdown(bid, bname, 'global_tag', 'Global', cur, ['GLOBAL', 'NO GLOBAL']))
                    global_lay.addWidget(global_label, 1)
                    global_lay.addWidget(global_edit_btn)
                    self.branch_table.setCellWidget(row_idx, 6, global_widget)

                    # Sunday column (col 7) with edit button
                    sunday_val = row_data.get('sunday', '') or ''
                    sunday_widget = QWidget()
                    sunday_lay = QHBoxLayout(sunday_widget)
                    sunday_lay.setContentsMargins(2, 2, 2, 2)
                    sunday_lay.setSpacing(4)
                    sunday_label = QLabel(sunday_val if sunday_val else '—')
                    sunday_label.setStyleSheet("font-size:10px; color: #2c3e50;" if sunday_val else "font-size:10px; color: #aaa;")
                    sunday_edit_btn = QPushButton("✏️")
                    sunday_edit_btn.setFixedSize(24, 24)
                    sunday_edit_btn.setToolTip("Edit Sunday")
                    sunday_edit_btn.setStyleSheet("QPushButton { background: #3498db; border: none; border-radius: 3px; } QPushButton:hover { background: #2980b9; }")
                    sunday_edit_btn.clicked.connect(lambda checked, bid=row_data['id'], bname=row_data.get('name', ''), cur=sunday_val: self._edit_branch_dropdown(bid, bname, 'sunday', 'Sunday', cur, ['YES', 'NO']))
                    sunday_lay.addWidget(sunday_label, 1)
                    sunday_lay.addWidget(sunday_edit_btn)
                    self.branch_table.setCellWidget(row_idx, 7, sunday_widget)

                    # LOB column (col 8) with edit button
                    lob_val = row_data.get('line_of_business', '') or ''
                    lob_widget = QWidget()
                    lob_lay = QHBoxLayout(lob_widget)
                    lob_lay.setContentsMargins(2, 2, 2, 2)
                    lob_lay.setSpacing(4)
                    lob_label = QLabel(lob_val if lob_val else '—')
                    lob_label.setStyleSheet("font-size:10px; color: #2c3e50;" if lob_val else "font-size:10px; color: #aaa;")
                    lob_edit_btn = QPushButton("✏️")
                    lob_edit_btn.setFixedSize(24, 24)
                    lob_edit_btn.setToolTip("Edit Line of Business")
                    lob_edit_btn.setStyleSheet("QPushButton { background: #3498db; border: none; border-radius: 3px; } QPushButton:hover { background: #2980b9; }")
                    lob_edit_btn.clicked.connect(lambda checked, bid=row_data['id'], bname=row_data.get('name', ''), cur=lob_val: self._edit_branch_dropdown(bid, bname, 'line_of_business', 'Line of Business', cur, ['GROUP 1', 'GROUP 2', 'GROUP 3']))
                    lob_lay.addWidget(lob_label, 1)
                    lob_lay.addWidget(lob_edit_btn)
                    self.branch_table.setCellWidget(row_idx, 8, lob_widget)

                    self.branch_table.setItem(row_idx, 9, QTableWidgetItem(str(row_data.get('created_at', ''))[:19]))
                    
                    is_registered = row_data.get('is_registered', 1)
                    reg_widget = QWidget()
                    reg_layout = QHBoxLayout(reg_widget)
                    reg_layout.setContentsMargins(2, 2, 2, 2)
                    reg_layout.setSpacing(6)

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

                    reg_btn.clicked.connect(lambda checked, bid=row_data['id'], current=is_registered, bname=row_data.get('name', ''): self._toggle_branch_registered(bid, current, bname))

                    reg_layout.addWidget(status_label)
                    reg_layout.addWidget(reg_btn)
                    reg_layout.addStretch()
                    self.branch_table.setCellWidget(row_idx, 10, reg_widget)
                    
                    action_widget = QWidget()
                    action_layout = QHBoxLayout(action_widget)
                    action_layout.setContentsMargins(2, 2, 2, 2)
                    action_layout.setSpacing(2)
                    
                    del_btn = QPushButton("🗑️")
                    del_btn.setFixedSize(28, 24)
                    del_btn.setStyleSheet("QPushButton { background: #e74c3c; border: none; border-radius: 3px; } QPushButton:hover { background: #c0392b; }")
                    del_btn.clicked.connect(lambda checked, bid=row_data['id'], bname=row_data['name']: self._delete_branch(bid, bname))
                    
                    action_layout.addWidget(del_btn)
                    self.branch_table.setCellWidget(row_idx, 11, action_widget)
            
            self.branch_page_label.setText(f"Page {self.branch_page + 1} of {total_pages} ({self.branch_total} total)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load branches: {e}")

    def _edit_branch_os(self, branch_id, branch_name, current_os):
        """Open a dialog to assign / change the Operation Supervisor for a branch."""
        from PyQt5.QtWidgets import QInputDialog
        supervisors = get_all_supervisors()
        items = ['-- Clear --'] + [s['name'] for s in supervisors]
        current_idx = 0
        if current_os:
            for i, s in enumerate(supervisors):
                if s['name'] == current_os:
                    current_idx = i + 1
                    break
        new_os, ok = QInputDialog.getItem(
            self, "Assign Operation Supervisor",
            f"Select OS for branch '{branch_name}':",
            items, current_idx, False
        )
        if not ok:
            return
        if new_os == '-- Clear --':
            new_os = None
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

    def _edit_branch_corporations(self, branch_id, branch_name, main_corp_id, sub_corp_id):
        """Open a dialog to edit main and sub corporation for a branch."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Corporations - {branch_name}")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        layout.setSpacing(10)
        
        # Load all corporations
        try:
            corps = self.db.execute_query("SELECT id, name FROM corporations ORDER BY name")
        except:
            corps = []
        
        # Main Corporation combo
        main_corp_combo = QComboBox()
        for c in corps:
            main_corp_combo.addItem(c['name'], c['id'])
            if c['id'] == main_corp_id:
                main_corp_combo.setCurrentIndex(main_corp_combo.count() - 1)
        
        # Sub Corporation combo
        sub_corp_combo = QComboBox()
        sub_corp_combo.addItem("-- None --", None)
        for c in corps:
            sub_corp_combo.addItem(c['name'], c['id'])
            if c['id'] == sub_corp_id:
                sub_corp_combo.setCurrentIndex(sub_corp_combo.count() - 1)
        
        layout.addRow("Main Corporation:", main_corp_combo)
        layout.addRow("Sub Corporation:", sub_corp_combo)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                new_main_corp_id = main_corp_combo.currentData()
                new_sub_corp_id = sub_corp_combo.currentData()
                
                if new_sub_corp_id and new_sub_corp_id == new_main_corp_id:
                    QMessageBox.warning(self, "Invalid", "Sub Corporation must be different from Main Corporation.")
                    return
                
                # Update in database
                self.db.execute_query(
                    "UPDATE branches SET corporation_id = %s, sub_corporation_id = %s WHERE id = %s",
                    (new_main_corp_id, new_sub_corp_id, branch_id)
                )
                
                main_corp_name = main_corp_combo.currentText()
                sub_corp_name = sub_corp_combo.currentText() if new_sub_corp_id else "None"
                QMessageBox.information(self, "✅ Updated", 
                    f"Branch '{branch_name}' updated:\nMain: {main_corp_name}\nSub: {sub_corp_name}")
                self._load_branches()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update corporations: {e}")

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

    def _edit_branch_field(self, branch_id, branch_name, field_name, field_label, current_value):
        """Open a dialog to edit a text field for a branch."""
        from PyQt5.QtWidgets import QInputDialog
        new_val, ok = QInputDialog.getText(
            self, f"Edit {field_label}",
            f"Enter {field_label} for branch '{branch_name}':",
            text=current_value or ""
        )
        if not ok:
            return
        new_val = new_val.strip()
        try:
            self.db.execute_query(
                f"UPDATE branches SET {field_name} = %s WHERE id = %s",
                (new_val if new_val else None, branch_id)
            )
            QMessageBox.information(self, "Updated",
                f"{field_label} for '{branch_name}' set to '{new_val}'." if new_val else f"{field_label} for '{branch_name}' cleared.")
            self._load_branches()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update {field_label}: {e}")

    def _edit_branch_dropdown(self, branch_id, branch_name, field_name, field_label, current_value, options):
        """Open a dialog to edit a dropdown field for a branch."""
        from PyQt5.QtWidgets import QInputDialog
        # Add empty option for clearing
        items = ['-- Clear --'] + options
        current_idx = 0
        if current_value in options:
            current_idx = options.index(current_value) + 1
        
        new_val, ok = QInputDialog.getItem(
            self, f"Edit {field_label}",
            f"Select {field_label} for branch '{branch_name}':",
            items, current_idx, False
        )
        if not ok:
            return
        
        # Handle clear option
        if new_val == '-- Clear --':
            new_val = None
        
        try:
            self.db.execute_query(
                f"UPDATE branches SET {field_name} = %s WHERE id = %s",
                (new_val, branch_id)
            )
            QMessageBox.information(self, "Updated",
                f"{field_label} for '{branch_name}' set to '{new_val}'." if new_val else f"{field_label} for '{branch_name}' cleared.")
            self._load_branches()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update {field_label}: {e}")

    def _load_clients(self):
        """Load clients with pagination and search"""
        try:
            search = self.client_search_input.text().strip()
            
            # Build query
            if search:
                count_query = "SELECT COUNT(*) as cnt FROM users WHERE role='user' AND (username LIKE %s OR branch LIKE %s)"
                search_param = f"%{search}%"
                count_row = self.db.execute_query(count_query, (search_param, search_param))
            else:
                count_row = self.db.execute_query("SELECT COUNT(*) as cnt FROM users WHERE role='user'")
            
            self.client_total = count_row[0]['cnt'] if count_row else 0
            
            total_pages = max(1, (self.client_total + self.page_size - 1) // self.page_size)
            self.client_page = min(self.client_page, total_pages - 1)
            self.client_page = max(0, self.client_page)
            
            offset = self.client_page * self.page_size
            
            if search:
                rows = self.db.execute_query("""
                    SELECT id, username, corporation, branch, created_at
                    FROM users WHERE role='user' AND (username LIKE %s OR branch LIKE %s)
                    ORDER BY id DESC LIMIT %s OFFSET %s
                """, (search_param, search_param, self.page_size, offset))
            else:
                rows = self.db.execute_query("""
                    SELECT id, username, corporation, branch, created_at
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
                    self.client_table.setItem(row_idx, 2, QTableWidgetItem(str(row_data.get('corporation', ''))))
                    self.client_table.setItem(row_idx, 3, QTableWidgetItem(str(row_data.get('branch', ''))))
                    self.client_table.setItem(row_idx, 4, QTableWidgetItem(str(row_data.get('created_at', ''))[:19]))
                    
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
                    self.client_table.setCellWidget(row_idx, 5, action_widget)
            
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
        corp_id2 = self.branch_corp_combo2.currentData()
        os_name = self.branch_os_combo.currentData()
        area = self.branch_area_input.text().strip() or None
        global_tag = self.branch_global_combo.currentData()
        sunday = self.branch_sunday_combo.currentData()
        lob = self.branch_lob_combo.currentData()
        
        missing = []
        if not corp_id:
            missing.append("Corporation")
        if not name:
            missing.append("Branch Name")
        if not os_name:
            missing.append("Group")
        if not area:
            missing.append("Area")
        if not global_tag:
            missing.append("Global")
        if not sunday:
            missing.append("Sunday")
        if not lob:
            missing.append("LOB")
        if missing:
            QMessageBox.warning(self, "Input Required", f"Please fill in the following fields:\n• " + "\n• ".join(missing))
            return
        if corp_id2 and corp_id2 == corp_id:
            QMessageBox.warning(self, "Same Corporation", "Sub Corporation must be different from Main Corporation.")
            return
        
        # Check duplicates for corp 1
        existing = self.db.execute_query(
            "SELECT id FROM branches WHERE corporation_id = %s AND name = %s",
            (corp_id, name)
        )
        if existing:
            corp_name = self.branch_corp_combo.currentText()
            QMessageBox.warning(self, "Duplicate Branch", f"Branch '{name}' already exists under '{corp_name}'.")
            return
        
        try:
            # Create only ONE branch with the main corporation
            bid = create_branch(name, corp_id, os_name=os_name, sub_corporation_id=corp_id2)
            
            if bid:
                # Update all additional fields
                self.db.execute_query(
                    """UPDATE branches 
                       SET area = %s, global_tag = %s, sunday = %s, line_of_business = %s 
                       WHERE id = %s""",
                    (area, global_tag, sunday, lob, bid)
                )
            
            if bid:
                corp_name = self.branch_corp_combo.currentText()
                if corp_id2:
                    sub_corp_name = self.branch_corp_combo2.currentText()
                    QMessageBox.information(self, "✅ Created", f"Branch '{name}' created under {corp_name} (ID: {bid})\nSub Corporation: {sub_corp_name}")
                else:
                    QMessageBox.information(self, "✅ Created", f"Branch '{name}' created (ID: {bid})")
            
            self.branch_name_input.clear()
            self.branch_os_combo.setCurrentIndex(0)
            self.branch_area_input.clear()
            self.branch_global_combo.setCurrentIndex(0)
            self.branch_sunday_combo.setCurrentIndex(0)
            self.branch_lob_combo.setCurrentIndex(0)
            self.branch_corp_combo2.setCurrentIndex(0)
            self._load_branches()
            self._refresh_client_branches()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create branch: {e}")

    def _add_client(self):
        corp_id = self.client_corp_combo.currentData()
        branch_id = self.client_branch_combo.currentData()
        password = self.client_password_input.text() or None

        if not corp_id or not branch_id:
            QMessageBox.warning(self, "Selection Required", "Please select corporation and branch.")
            return

        try:
            row = create_client(None, None, corp_id, branch_id, password)
            if row:
                QMessageBox.information(self, "✅ Created", f"Client created!\nUsername: {row['username']}\nID: {row['id']}")
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
                    branches = self.db.execute_query("SELECT id, name FROM branches WHERE corporation_id = %s OR sub_corporation_id = %s ORDER BY name", (corp_id, corp_id))
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
        
        pw_row = QHBoxLayout()
        pw_row.addWidget(password_input)
        edit_show_pw = QCheckBox("Show")
        edit_show_pw.toggled.connect(lambda checked: password_input.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password))
        pw_row.addWidget(edit_show_pw)
        
        layout.addRow("Username:", username_label)
        layout.addRow("Corporation:", corp_combo)
        layout.addRow("Branch:", branch_combo)
        layout.addRow("New Password:", pw_row)
        
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
                
                new_corp = corp_combo.currentText()
                new_branch = branch_combo.currentText()
                new_password = password_input.text()
                
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
        
        self.admin_show_pw = QCheckBox("Show")
        self.admin_show_pw.toggled.connect(lambda checked: self.admin_password_input.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password))

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
        form_layout.addWidget(self.admin_show_pw)
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
        
        reset_show_pw = QCheckBox("Show")
        reset_show_pw.toggled.connect(lambda checked: (
            new_pw.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password),
            confirm_pw.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        ))

        form.addRow("New Password:", new_pw)
        form.addRow("Confirm:", confirm_pw)
        form.addRow("", reset_show_pw)

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
                    self, "Updated",
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
                QMessageBox.information(self, "Deleted", f"Client '{username}' deleted.")
                self._load_clients()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    # ========== OPERATION SUPERVISORS ==========

    def _load_os_dropdown(self):
        """Populate the OS dropdown in the branch creation form."""
        current = self.branch_os_combo.currentData()
        self.branch_os_combo.clear()
        self.branch_os_combo.addItem("-- Select Group --", None)
        try:
            supervisors = get_all_supervisors()
            for s in supervisors:
                self.branch_os_combo.addItem(s['name'], s['name'])
            if current:
                idx = self.branch_os_combo.findData(current)
                if idx >= 0:
                    self.branch_os_combo.setCurrentIndex(idx)
        except Exception as e:
            print(f"Error loading supervisors: {e}")

    def _build_os_tab(self):

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("📋 Manage Operation Supervisors")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        desc = QLabel("Add or remove Operation Supervisor names. These will appear as dropdown options when creating branches.")
        desc.setStyleSheet("font-size: 12px; color: #666;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Add form
        add_frame = QFrame()
        add_frame.setStyleSheet("QFrame { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 12px; }")
        add_layout = QHBoxLayout(add_frame)
        add_layout.setSpacing(10)

        self._os_name_input = QLineEdit()
        self._os_name_input.setPlaceholderText("Enter Operation Supervisor name")
        self._os_name_input.setStyleSheet("QLineEdit { padding: 8px; border: 1.5px solid #ccc; border-radius: 6px; font-size: 13px; } QLineEdit:focus { border-color: #3498db; }")
        self._os_name_input.returnPressed.connect(self._on_add_supervisor)
        add_layout.addWidget(self._os_name_input, 1)

        add_btn = QPushButton("➕ Add Supervisor")
        add_btn.setStyleSheet("QPushButton { background: #27ae60; color: white; border: none; padding: 8px 18px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: #229954; }")
        add_btn.clicked.connect(self._on_add_supervisor)
        add_layout.addWidget(add_btn)
        layout.addWidget(add_frame)


        list_label = QLabel("Current Operation Supervisors:")
        list_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(list_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #dee2e6; border-radius: 6px; }")
        self._os_list_widget = QWidget()
        self._os_list_layout = QVBoxLayout(self._os_list_widget)
        self._os_list_layout.setAlignment(Qt.AlignTop)
        self._os_list_layout.setSpacing(6)
        scroll.setWidget(self._os_list_widget)
        layout.addWidget(scroll, 1)

        self._refresh_os_list()
        return widget

    def _refresh_os_list(self):
        """Reload the operation supervisors list UI."""
        while self._os_list_layout.count():
            item = self._os_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        supervisors = get_all_supervisors()
        if not supervisors:
            empty = QLabel("No operation supervisors added yet.")
            empty.setStyleSheet("color: #999; font-style: italic; padding: 20px;")
            empty.setAlignment(Qt.AlignCenter)
            self._os_list_layout.addWidget(empty)
            return

        for sup in supervisors:
            sid = sup['id']
            sname = sup['name']
            row = QFrame()
            row.setStyleSheet("QFrame { background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 10px; } QFrame:hover { border-color: #3498db; }")
            h = QHBoxLayout(row)
            h.setContentsMargins(10, 6, 10, 6)
            lbl = QLabel(f"👤 {sname}")
            lbl.setStyleSheet("font-size: 13px; font-weight: 600; border: none;")
            h.addWidget(lbl)
            h.addStretch()

            edit_btn = QPushButton("✏️ Edit")
            edit_btn.setStyleSheet("QPushButton { background: #3498db; color: white; border: none; padding: 5px 12px; border-radius: 4px; font-size: 11px; font-weight: bold; } QPushButton:hover { background: #2980b9; }")
            edit_btn.clicked.connect(lambda checked, s_id=sid, s_name=sname: self._on_edit_supervisor(s_id, s_name))
            h.addWidget(edit_btn)

            del_btn = QPushButton("🗑️ Remove")
            del_btn.setStyleSheet("QPushButton { background: #e74c3c; color: white; border: none; padding: 5px 12px; border-radius: 4px; font-size: 11px; font-weight: bold; } QPushButton:hover { background: #c0392b; }")
            del_btn.clicked.connect(lambda checked, s_id=sid, s_name=sname: self._on_delete_supervisor(s_id, s_name))
            h.addWidget(del_btn)
            self._os_list_layout.addWidget(row)

    def _on_add_supervisor(self):
        name = self._os_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Required", "Please enter a supervisor name.")
            return
        try:
            sid = create_supervisor(name)
            if sid:
                QMessageBox.information(self, "✅ Created", f"Operation Supervisor '{name}' added.")
                self._os_name_input.clear()
                self._refresh_os_list()
                self._load_os_dropdown()
        except Exception as e:
            if "Duplicate" in str(e):
                QMessageBox.warning(self, "Duplicate", f"'{name}' already exists.")
            else:
                QMessageBox.critical(self, "Error", f"Failed to add supervisor: {e}")

    def _on_delete_supervisor(self, supervisor_id, name):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to remove '{name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                delete_supervisor(supervisor_id)
                self._refresh_os_list()
                self._load_os_dropdown()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove supervisor: {e}")

    def _on_edit_supervisor(self, supervisor_id, current_name):
        from PyQt5.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self, "Edit Supervisor",
            "Enter new name:",
            text=current_name
        )
        if not ok:
            return
        new_name = new_name.strip()
        if not new_name or new_name == current_name:
            return
        try:
            update_supervisor(supervisor_id, new_name)
            self._refresh_os_list()
            self._load_os_dropdown()
        except Exception as e:
            if "Duplicate" in str(e):
                QMessageBox.warning(self, "Duplicate", f"'{new_name}' already exists.")
            else:
                QMessageBox.critical(self, "Error", f"Failed to rename supervisor: {e}")
