"""
Machine Management Page — Super Admin Dashboard

Lists all registered machines with their approval status.
Super admin can revoke, approve, or bulk-approve all pending machines.
"""
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFrame, QLineEdit, QComboBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont

logger = logging.getLogger(__name__)

_GREEN = "#16A34A"
_RED   = "#DC2626"
_AMBER = "#D97706"


# ── Background workers ────────────────────────────────────────────────────────

class _LoadWorker(QThread):
    done    = pyqtSignal(list)
    error   = pyqtSignal(str)

    def run(self):
        try:
            import requests
            from api_config import API_URL, API_KEY
            tok = _get_token(API_URL, API_KEY)
            resp = requests.get(
                f"{API_URL}/api/machine/list",
                headers={"Authorization": f"Bearer {tok}"},
                timeout=10,
            )
            if resp.status_code == 200:
                self.done.emit(resp.json().get("machines", []))
            else:
                self.error.emit(f"machine/list returned HTTP {resp.status_code}")
        except Exception as exc:
            self.error.emit(str(exc))


class _ActionWorker(QThread):
    done    = pyqtSignal()
    error   = pyqtSignal(str)

    def __init__(self, action: str, machine_ids: list, parent=None):
        super().__init__(parent)
        self._action = action
        self._machine_ids = machine_ids

    def run(self):
        try:
            import requests
            from api_config import API_URL, API_KEY
            tok = _get_token(API_URL, API_KEY)
            headers = {"Authorization": f"Bearer {tok}"}
            failed = []
            for mid in self._machine_ids:
                resp = requests.post(
                    f"{API_URL}/api/machine/{self._action}/{mid}",
                    headers=headers,
                    timeout=5,
                )
                if resp.status_code != 200:
                    failed.append(mid)
            if failed:
                self.error.emit(f"{len(failed)} machine(s) failed to {self._action}.")
            else:
                self.done.emit()
        except Exception as exc:
            self.error.emit(str(exc))


def _get_token(api_url: str, api_key: str) -> str:
    import requests
    return requests.post(
        f"{api_url}/api/token", json={"api_key": api_key}, timeout=5
    ).json().get("token", "")


# ── Page ─────────────────────────────────────────────────────────────────────

class MachinePage(QWidget):

    _PAGE_SIZE = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self._machines         = []
        self._filtered_machines = []
        self._current_page     = 1
        self._worker           = None   # keep reference so GC doesn't kill the thread
        self._build_ui()
        self._load()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Registered Machines")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #1E293B;")
        title_row.addWidget(title)
        title_row.addStretch()

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search hostname / branch / user…")
        self._search.setFixedWidth(240)
        self._search.setStyleSheet(
            "border:1px solid #CBD5E1; border-radius:6px; padding:6px 10px; font-size:12px;"
        )
        self._search.textChanged.connect(self._filter)
        title_row.addWidget(self._search)

        self._status_filter = QComboBox()
        self._status_filter.addItems(["All", "Approved", "Pending", "Revoked"])
        self._status_filter.setFixedWidth(110)
        self._status_filter.setStyleSheet(
            "border:1px solid #CBD5E1; border-radius:6px; padding:5px 8px; font-size:12px;"
        )
        self._status_filter.currentIndexChanged.connect(self._filter)
        title_row.addWidget(self._status_filter)

        self._approve_all_btn = QPushButton("Approve All Pending")
        self._approve_all_btn.setStyleSheet(
            "QPushButton{background:#FEF3C7;color:#92400E;border:1px solid #F59E0B;"
            "border-radius:6px;padding:6px 14px;font-weight:700;font-size:12px;}"
            "QPushButton:hover{background:#FDE68A;}"
            "QPushButton:disabled{background:#F1F5F9;color:#94A3B8;border-color:#E2E8F0;}"
        )
        self._approve_all_btn.setEnabled(False)
        self._approve_all_btn.clicked.connect(self._approve_all_pending)
        title_row.addWidget(self._approve_all_btn)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setStyleSheet(
            "QPushButton{background:#3B82F6;color:white;border:none;border-radius:6px;"
            "padding:6px 16px;font-weight:700;font-size:12px;}"
            "QPushButton:hover{background:#2563EB;}"
            "QPushButton:disabled{background:#93C5FD;color:white;border:none;}"
        )
        self._refresh_btn.clicked.connect(self._load)
        title_row.addWidget(self._refresh_btn)
        root.addLayout(title_row)

        # Summary bar
        self._summary = QLabel("Loading…")
        self._summary.setStyleSheet("font-size: 12px; color: #64748B;")
        root.addWidget(self._summary)

        # Table
        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels([
            "Hostname", "Branch", "User", "MAC Address",
            "Status", "Registered", "Action"
        ])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setSortingEnabled(False)
        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E2E8F0; border-radius: 8px;
                gridline-color: #F1F5F9;
            }
            QHeaderView::section {
                background: #F8FAFC; font-weight: 700; font-size: 11px;
                padding: 8px 10px; border: none;
                border-bottom: 2px solid #E2E8F0;
            }
            QTableWidget::item { padding: 6px 10px; }
        """)
        root.addWidget(self._table)

        # Pagination controls
        page_row = QHBoxLayout()
        page_row.addStretch()

        self._prev_btn = QPushButton("◀ Prev")
        self._prev_btn.setFixedWidth(80)
        self._prev_btn.setStyleSheet(
            "QPushButton{background:#F1F5F9;color:#1E293B;border:1px solid #CBD5E1;"
            "border-radius:6px;padding:5px 10px;font-weight:700;font-size:12px;}"
            "QPushButton:hover{background:#E2E8F0;}"
            "QPushButton:disabled{color:#CBD5E1;border-color:#E2E8F0;}"
        )
        self._prev_btn.clicked.connect(self._prev_page)
        page_row.addWidget(self._prev_btn)

        self._page_label = QLabel("Page 1 of 1")
        self._page_label.setStyleSheet("font-size:12px;color:#475569;font-weight:600;padding:0 12px;")
        self._page_label.setAlignment(Qt.AlignCenter)
        page_row.addWidget(self._page_label)

        self._next_btn = QPushButton("Next ▶")
        self._next_btn.setFixedWidth(80)
        self._next_btn.setStyleSheet(
            "QPushButton{background:#F1F5F9;color:#1E293B;border:1px solid #CBD5E1;"
            "border-radius:6px;padding:5px 10px;font-weight:700;font-size:12px;}"
            "QPushButton:hover{background:#E2E8F0;}"
            "QPushButton:disabled{color:#CBD5E1;border-color:#E2E8F0;}"
        )
        self._next_btn.clicked.connect(self._next_page)
        page_row.addWidget(self._next_btn)

        page_row.addStretch()
        root.addLayout(page_row)

    # ── Data (background thread) ──────────────────────────────────────────────

    def _load(self):
        self._set_busy(True)
        self._worker = _LoadWorker()
        self._worker.done.connect(self._on_loaded)
        self._worker.error.connect(self._on_load_error)
        self._worker.start()

    def _on_loaded(self, machines: list):
        self._machines = machines
        self._filter()
        self._set_busy(False)

    def _on_load_error(self, msg: str):
        logger.error("Failed to load machines: %s", msg)
        self._summary.setText(f"Error: {msg}")
        self._set_busy(False)

    def _set_busy(self, busy: bool):
        self._refresh_btn.setEnabled(not busy)
        self._approve_all_btn.setEnabled(not busy)
        if busy:
            self._refresh_btn.setText("Loading…")
        else:
            self._refresh_btn.setText("Refresh")

    # ── Filter / populate ─────────────────────────────────────────────────────

    def _filter(self):
        query  = self._search.text().lower()
        status = self._status_filter.currentText().lower()

        visible = []
        for m in self._machines:
            if status != "all" and m.get("status", "") != status:
                continue
            haystack = " ".join([
                str(m.get("hostname")    or ""),
                str(m.get("branch")      or ""),
                str(m.get("username")    or ""),
                str(m.get("mac_address") or ""),
            ]).lower()
            if query and query not in haystack:
                continue
            visible.append(m)

        self._filtered_machines = visible
        self._current_page = 1
        self._render_page()

        total    = len(self._machines)
        approved = sum(1 for m in self._machines if m.get("status") == "approved")
        pending  = sum(1 for m in self._machines if m.get("status") == "pending")
        revoked  = sum(1 for m in self._machines if m.get("status") == "revoked")
        self._summary.setText(
            f"{total} machine(s) total  •  "
            f"<span style='color:{_GREEN}'>{approved} approved</span>  •  "
            f"<span style='color:{_AMBER}'>{pending} pending</span>  •  "
            f"<span style='color:{_RED}'>{revoked} revoked</span>"
        )
        self._summary.setTextFormat(Qt.RichText)

        self._approve_all_btn.setEnabled(pending > 0 and self._refresh_btn.isEnabled())
        self._approve_all_btn.setText(
            f"Approve All Pending ({pending})" if pending > 0 else "Approve All Pending"
        )

    def _render_page(self):
        total_pages = max(1, (len(self._filtered_machines) + self._PAGE_SIZE - 1) // self._PAGE_SIZE)
        self._current_page = max(1, min(self._current_page, total_pages))

        start = (self._current_page - 1) * self._PAGE_SIZE
        end   = start + self._PAGE_SIZE
        self._populate(self._filtered_machines[start:end])

        self._page_label.setText(f"Page {self._current_page} of {total_pages}")
        self._prev_btn.setEnabled(self._current_page > 1)
        self._next_btn.setEnabled(self._current_page < total_pages)

    def _prev_page(self):
        if self._current_page > 1:
            self._current_page -= 1
            self._render_page()

    def _next_page(self):
        total_pages = max(1, (len(self._filtered_machines) + self._PAGE_SIZE - 1) // self._PAGE_SIZE)
        if self._current_page < total_pages:
            self._current_page += 1
            self._render_page()

    def _populate(self, machines: list):
        tbl = self._table
        tbl.setUpdatesEnabled(False)
        tbl.setSortingEnabled(False)
        tbl.setRowCount(0)

        bold = QFont()
        bold.setBold(True)

        for m in machines:
            row = tbl.rowCount()
            tbl.insertRow(row)

            status = m.get("status", "unknown")
            reg    = (m.get("registered_at") or "")[:10]
            status_color = (
                _GREEN if status == "approved" else
                _AMBER if status == "pending"  else _RED
            )

            for col, text in enumerate([
                m.get("hostname")    or "—",
                m.get("branch")      or "—",
                m.get("username")    or "—",
                m.get("mac_address") or "—",
                status.upper(),
                reg,
            ]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if col == 4:
                    item.setForeground(QColor(status_color))
                    item.setFont(bold)
                tbl.setItem(row, col, item)

            # Action buttons
            cell_widget = QWidget()
            btn_layout = QHBoxLayout(cell_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)

            if status != "approved":
                approve_btn = QPushButton("Approve")
                approve_btn.setStyleSheet(
                    "QPushButton{background:#DCFCE7;color:#16A34A;border:none;"
                    "border-radius:5px;padding:4px 10px;font-weight:700;font-size:11px;}"
                    "QPushButton:hover{background:#BBF7D0;}"
                )
                approve_btn.clicked.connect(
                    lambda _, mid=m["machine_id"], h=m.get("hostname", ""): self._approve(mid, h)
                )
                btn_layout.addWidget(approve_btn)

            if status != "revoked":
                revoke_btn = QPushButton("Revoke")
                revoke_btn.setStyleSheet(
                    "QPushButton{background:#FEE2E2;color:#DC2626;border:none;"
                    "border-radius:5px;padding:4px 10px;font-weight:700;font-size:11px;}"
                    "QPushButton:hover{background:#FECACA;}"
                )
                revoke_btn.clicked.connect(
                    lambda _, mid=m["machine_id"], h=m.get("hostname", ""): self._revoke(mid, h)
                )
                btn_layout.addWidget(revoke_btn)

            tbl.setCellWidget(row, 6, cell_widget)

        tbl.setUpdatesEnabled(True)
        tbl.resizeRowsToContents()

    # ── Actions (background thread) ───────────────────────────────────────────

    def _revoke(self, machine_id: str, hostname: str):
        r = QMessageBox.question(
            self, "Revoke Machine",
            f"Revoke access for <b>{hostname or machine_id}</b>?<br><br>"
            "The machine will be blocked on the next app launch.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if r != QMessageBox.Yes:
            return
        self._run_action("revoke", [machine_id])

    def _approve(self, machine_id: str, hostname: str):
        self._run_action("approve", [machine_id])

    def _approve_all_pending(self):
        pending = [m["machine_id"] for m in self._machines if m.get("status") == "pending"]
        if not pending:
            return
        r = QMessageBox.question(
            self, "Approve All Pending",
            f"Approve all <b>{len(pending)}</b> pending machine(s)?<br><br>"
            "These machines will be allowed to use the application immediately.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if r != QMessageBox.Yes:
            return
        self._run_action("approve", pending)

    def _run_action(self, action: str, machine_ids: list):
        self._set_busy(True)
        worker = _ActionWorker(action, machine_ids)
        worker.done.connect(lambda: self._on_action_done(worker))
        worker.error.connect(lambda msg: self._on_action_error(worker, msg))
        # Keep reference alive until finished
        worker._keep_alive = worker
        worker.start()

    def _on_action_done(self, worker):
        worker._keep_alive = None
        self._load()

    def _on_action_error(self, worker, msg: str):
        worker._keep_alive = None
        QMessageBox.warning(self, "Error", msg)
        self._load()
