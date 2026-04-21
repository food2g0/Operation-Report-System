"""
Review Summary Page
Shows reviewed / pending review status of all branch entries for a given date.
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QComboBox, QPushButton, QMessageBox, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from db_connect_pooled import db_manager


class ReviewSummaryPage(QWidget):
    """Review summary widget showing reviewed / pending branches."""

    def __init__(self, account_type=2):
        super().__init__()
        self.account_type = account_type
        self.db = db_manager
        self.daily_table = "daily_reports_brand_a" if account_type == 1 else "daily_reports"
        self._page = 0
        self._page_size = 20
        self._all_rows = []       # full filtered result
        self._display_rows = []   # after branch search applied
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Title
        title = QLabel("📊 Review Summary")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # Filters bar
        filter_frame = QFrame()
        filter_frame.setStyleSheet("QFrame { background: #f8f9fa; border-radius: 6px; padding: 8px; }")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setSpacing(10)

        # Date picker
        filter_layout.addWidget(QLabel("Date:"))
        self._date = QDateEdit()
        self._date.setCalendarPopup(True)
        self._date.setDate(QDate.currentDate())
        self._date.setDisplayFormat("yyyy-MM-dd")
        self._date.setMinimumWidth(130)
        filter_layout.addWidget(self._date)

        # Corporation filter
        filter_layout.addWidget(QLabel("Corporation:"))
        self._corp_combo = QComboBox()
        self._corp_combo.setMinimumWidth(160)
        self._corp_combo.addItem("All Corporations", None)
        try:
            corps = self.db.execute_query("SELECT name FROM corporations ORDER BY name")
            if corps:
                for c in corps:
                    self._corp_combo.addItem(c['name'], c['name'])
        except Exception:
            pass
        filter_layout.addWidget(self._corp_combo)

        # Group (OS) filter
        filter_layout.addWidget(QLabel("Group:"))
        self._group_combo = QComboBox()
        self._group_combo.setMinimumWidth(160)
        self._group_combo.addItem("All Groups", None)
        try:
            os_rows = self.db.execute_query(
                "SELECT DISTINCT os_name FROM branches WHERE os_name IS NOT NULL AND os_name != '' ORDER BY os_name"
            )
            if os_rows:
                for r in os_rows:
                    self._group_combo.addItem(r['os_name'], r['os_name'])
        except Exception:
            pass
        filter_layout.addWidget(self._group_combo)

        # Status filter
        filter_layout.addWidget(QLabel("Status:"))
        self._status_combo = QComboBox()
        self._status_combo.addItem("All", "all")
        self._status_combo.addItem("Reviewed", "reviewed")
        self._status_combo.addItem("Pending", "pending")
        self._status_combo.addItem("No Entry", "no_entry")
        self._status_combo.setMinimumWidth(110)
        filter_layout.addWidget(self._status_combo)

        # Load button
        load_btn = QPushButton("🔄 Load")
        load_btn.setStyleSheet(
            "QPushButton { background: #3498db; color: white; padding: 6px 18px;"
            " border: none; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        load_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(load_btn)

        filter_layout.addStretch()
        layout.addWidget(filter_frame)

        # Search bar
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(8)

        search_layout.addWidget(QLabel("🔍 Search Branch:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Type branch name to filter...")
        self._search_input.setMaximumWidth(300)
        self._search_input.setStyleSheet(
            "QLineEdit { padding: 6px; border: 1.5px solid #ccc; border-radius: 4px; font-size: 12px; }"
            "QLineEdit:focus { border-color: #3498db; }"
        )
        self._search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self._search_input)
        search_layout.addStretch()
        layout.addWidget(search_frame)

        # Summary counters
        counter_frame = QFrame()
        counter_layout = QHBoxLayout(counter_frame)
        counter_layout.setContentsMargins(0, 0, 0, 0)
        counter_layout.setSpacing(10)

        self._total_label = QLabel("Total: 0")
        self._total_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #2c3e50; padding: 4px 10px; background: #ecf0f1; border-radius: 4px;")
        self._reviewed_label = QLabel("✅ Reviewed: 0")
        self._reviewed_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #27ae60; padding: 4px 10px; background: #eafaf1; border-radius: 4px;")
        self._pending_label = QLabel("⏳ Pending: 0")
        self._pending_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #e67e22; padding: 4px 10px; background: #fef9e7; border-radius: 4px;")
        self._noentry_label = QLabel("❌ No Entry: 0")
        self._noentry_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #e74c3c; padding: 4px 10px; background: #fdedec; border-radius: 4px;")

        counter_layout.addWidget(self._total_label)
        counter_layout.addWidget(self._reviewed_label)
        counter_layout.addWidget(self._pending_label)
        counter_layout.addWidget(self._noentry_label)
        counter_layout.addStretch()
        layout.addWidget(counter_frame)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Branch", "Corporation", "Group (OS)", "Status", "Reviewed At"])
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("""
            QTableWidget { background: white; gridline-color: #dee2e6; border: 1px solid #dee2e6; font-size: 11px; }
            QTableWidget::item { padding: 5px; }
            QHeaderView::section { background: #f8f9fa; padding: 8px; border: none; border-bottom: 2px solid #dee2e6; font-weight: bold; }
        """)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        layout.addWidget(self._table, 1)

        # Pagination controls
        pag_frame = QFrame()
        pag_layout = QHBoxLayout(pag_frame)
        pag_layout.setContentsMargins(0, 0, 0, 0)
        pag_layout.setSpacing(8)

        prev_btn = QPushButton("◀ Prev")
        prev_btn.setFixedWidth(80)
        prev_btn.setStyleSheet(
            "QPushButton { background: #3498db; color: white; border: none; padding: 5px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        prev_btn.clicked.connect(lambda: self._change_page(-1))

        next_btn = QPushButton("Next ▶")
        next_btn.setFixedWidth(80)
        next_btn.setStyleSheet(
            "QPushButton { background: #3498db; color: white; border: none; padding: 5px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        next_btn.clicked.connect(lambda: self._change_page(1))

        self._page_label = QLabel("Page 0 of 0")
        self._page_label.setStyleSheet("font-weight: bold; font-size: 11px;")

        pag_layout.addStretch()
        pag_layout.addWidget(prev_btn)
        pag_layout.addWidget(self._page_label)
        pag_layout.addWidget(next_btn)
        pag_layout.addStretch()
        layout.addWidget(pag_frame)

        # Auto-load
        self._load_data()

    # ── data ──────────────────────────────────────────────────────────────────

    def _load_data(self):
        """Fetch review data from DB and apply filters."""
        selected_date = self._date.date().toString("yyyy-MM-dd")
        brand_key = "A" if self.account_type == 1 else "B"
        corp_filter = self._corp_combo.currentData()
        group_filter = self._group_combo.currentData()
        status_filter = self._status_combo.currentData()

        try:
            branch_query = """
                SELECT b.name AS branch_name, c.name AS corp_name,
                       COALESCE(b.os_name, '') AS os_name
                FROM branches b
                LEFT JOIN corporations c ON b.corporation_id = c.id
                WHERE b.is_registered = 1
            """
            params = []
            if corp_filter:
                branch_query += " AND c.name = %s"
                params.append(corp_filter)
            if group_filter:
                branch_query += " AND b.os_name = %s"
                params.append(group_filter)
            branch_query += " ORDER BY c.name, b.name"

            branches = self.db.execute_query(branch_query, params) or []

            entry_query = f"SELECT DISTINCT branch FROM {self.daily_table} WHERE date = %s"
            entry_rows = self.db.execute_query(entry_query, [selected_date]) or []
            branches_with_entry = {r['branch'] for r in entry_rows}

            review_query = """
                SELECT branch, reviewed_at FROM admin_review_marks
                WHERE brand = %s AND report_date = %s
            """
            review_rows = self.db.execute_query(review_query, [brand_key, selected_date]) or []
            reviewed_map = {r['branch']: r['reviewed_at'] for r in review_rows}

            rows = []
            for b in branches:
                bname = b['branch_name']
                has_entry = bname in branches_with_entry
                is_reviewed = bname in reviewed_map
                reviewed_at = str(reviewed_map[bname])[:19] if is_reviewed else ""

                if has_entry and is_reviewed:
                    status = "reviewed"
                    status_text = "✅ Reviewed"
                elif has_entry and not is_reviewed:
                    status = "pending"
                    status_text = "⏳ Pending Review"
                else:
                    status = "no_entry"
                    status_text = "❌ No Entry"

                if status_filter != "all" and status != status_filter:
                    continue

                rows.append((bname, b['corp_name'] or '', b['os_name'] or '', status_text, reviewed_at, status))

            # Update counters (based on all branches, not filtered by status)
            total = len(branches)
            reviewed_count = sum(1 for b in branches if b['branch_name'] in reviewed_map)
            pending_count = sum(1 for b in branches if b['branch_name'] in branches_with_entry and b['branch_name'] not in reviewed_map)
            noentry_count = total - reviewed_count - pending_count

            self._total_label.setText(f"Total: {total}")
            self._reviewed_label.setText(f"✅ Reviewed: {reviewed_count}")
            self._pending_label.setText(f"⏳ Pending: {pending_count}")
            self._noentry_label.setText(f"❌ No Entry: {noentry_count}")

            self._all_rows = rows
            self._apply_search()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load review summary: {e}")

    # ── search ────────────────────────────────────────────────────────────────

    def _on_search_changed(self, text):
        self._apply_search()

    def _apply_search(self):
        """Filter _all_rows by branch search text, then render page 1."""
        search = self._search_input.text().strip().lower()
        if search:
            self._display_rows = [r for r in self._all_rows if search in r[0].lower()]
        else:
            self._display_rows = list(self._all_rows)
        self._page = 0
        self._render_page()

    # ── pagination ────────────────────────────────────────────────────────────

    def _change_page(self, delta):
        total_pages = max(1, (len(self._display_rows) + self._page_size - 1) // self._page_size)
        new_page = self._page + delta
        if 0 <= new_page < total_pages:
            self._page = new_page
            self._render_page()

    def _render_page(self):
        rows = self._display_rows
        total_pages = max(1, (len(rows) + self._page_size - 1) // self._page_size)
        self._page = max(0, min(self._page, total_pages - 1))
        start = self._page * self._page_size
        page_rows = rows[start:start + self._page_size]

        self._table.setRowCount(0)
        for row_data in page_rows:
            ri = self._table.rowCount()
            self._table.insertRow(ri)
            self._table.setItem(ri, 0, QTableWidgetItem(row_data[0]))
            self._table.setItem(ri, 1, QTableWidgetItem(row_data[1]))
            self._table.setItem(ri, 2, QTableWidgetItem(row_data[2]))

            status_item = QTableWidgetItem(row_data[3])
            if row_data[5] == "reviewed":
                status_item.setForeground(QColor('#27ae60'))
            elif row_data[5] == "pending":
                status_item.setForeground(QColor('#e67e22'))
            else:
                status_item.setForeground(QColor('#e74c3c'))
            self._table.setItem(ri, 3, status_item)
            self._table.setItem(ri, 4, QTableWidgetItem(row_data[4]))

        self._page_label.setText(f"Page {self._page + 1} of {total_pages} ({len(rows)} total)")
