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
        
        add_btn = QPushButton("➕ Add")
        add_btn.setStyleSheet("QPushButton { background: #27ae60; color: white; padding: 6px 16px; border: none; border-radius: 4px; font-weight: bold; } QPushButton:hover { background: #219a52; }")
        add_btn.clicked.connect(self._add_branch)
        
        form_layout.addWidget(QLabel("Corporation:"))
        form_layout.addWidget(self.branch_corp_combo)
        form_layout.addWidget(QLabel("Branch Name:"))
        form_layout.addWidget(self.branch_name_input)
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
        
        self.branch_page_label = QLabel("Page 0 of 0")
        prev_btn = QPushButton("◀")
        prev_btn.setFixedWidth(40)
        prev_btn.clicked.connect(lambda: self._change_branch_page(-1))
        next_btn = QPushButton("▶")
        next_btn.setFixedWidth(40)
        next_btn.clicked.connect(lambda: self._change_branch_page(1))
        
        control_bar.addWidget(show_btn)
        control_bar.addStretch()
        control_bar.addWidget(prev_btn)
        control_bar.addWidget(self.branch_page_label)
        control_bar.addWidget(next_btn)
        
        table_layout.addLayout(control_bar)
        
        # Table
        self.branch_table = QTableWidget()
        self.branch_table.setColumnCount(5)
        self.branch_table.setHorizontalHeaderLabels(["ID", "Branch Name", "Corporation", "Created At", "Actions"])
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
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
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
            if rows:
                for r in rows:
                    self.branch_corp_combo.addItem(r['name'], r['id'])
                    self.client_corp_combo.addItem(r['name'], r['id'])
        except Exception as e:
            print(f"Error loading corporations: {e}")

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

    def _load_branches(self):
        """Load branches with pagination"""
        try:
            count_row = self.db.execute_query("SELECT COUNT(*) as cnt FROM branches")
            self.branch_total = count_row[0]['cnt'] if count_row else 0
            
            total_pages = max(1, (self.branch_total + self.page_size - 1) // self.page_size)
            self.branch_page = min(self.branch_page, total_pages - 1)
            self.branch_page = max(0, self.branch_page)
            
            offset = self.branch_page * self.page_size
            rows = self.db.execute_query("""
                SELECT b.id, b.name, c.name as corp_name, b.created_at
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
                    self.branch_table.setItem(row_idx, 3, QTableWidgetItem(str(row_data.get('created_at', ''))[:19]))
                    
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
                    self.branch_table.setCellWidget(row_idx, 4, action_widget)
            
            self.branch_page_label.setText(f"Page {self.branch_page + 1} of {total_pages} ({self.branch_total} total)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load branches: {e}")

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
        if not corp_id:
            QMessageBox.warning(self, "Selection Required", "Please select a corporation.")
            return
        if not name:
            QMessageBox.warning(self, "Input Required", "Please enter a branch name.")
            return
        try:
            bid = create_branch(name, corp_id)
            if bid:
                QMessageBox.information(self, "✅ Created", f"Branch '{name}' created (ID: {bid})")
                self.branch_name_input.clear()
                self._load_branches()
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
