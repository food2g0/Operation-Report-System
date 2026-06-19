"""
Machine Management Page — Super Admin Dashboard

Lists all registered machines with their approval status.
Super admin can revoke, approve, or bulk-approve all pending machines.
"""
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFrame, QLineEdit, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

logger = logging.getLogger(__name__)

_GREEN = "#16A34A"
_RED   = "#DC2626"
_AMBER = "#D97706"


class MachinePage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._machines = []
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

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(
            "QPushButton{background:#3B82F6;color:white;border:none;border-radius:6px;"
            "padding:6px 16px;font-weight:700;font-size:12px;}"
            "QPushButton:hover{background:#2563EB;}"
        )
        refresh_btn.clicked.connect(self._load)
        title_row.addWidget(refresh_btn)
        root.addLayout(title_row)

        # Summary bar
        self._summary = QLabel("")
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

    # ── Data ─────────────────────────────────────────────────────────────────

    def _load(self):
        try:
            import requests
            from api_config import API_URL, API_KEY

            tok = requests.post(
                f"{API_URL}/api/token", json={"api_key": API_KEY}, timeout=5
            ).json().get("token", "")
            resp = requests.get(
                f"{API_URL}/api/machine/list",
                headers={"Authorization": f"Bearer {tok}"},
                timeout=8,
            )
            if resp.status_code == 200:
                self._machines = resp.json().get("machines", [])
                self._filter()
            else:
                logger.error("machine/list returned %s", resp.status_code)
        except Exception as exc:
            logger.error("Failed to load machines: %s", exc)
            QMessageBox.warning(self, "Error", f"Could not load machine list:\n{exc}")

    def _filter(self):
        query  = self._search.text().lower()
        status = self._status_filter.currentText().lower()   # all / approved / pending / revoked

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

        self._populate(visible)

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

        self._approve_all_btn.setEnabled(pending > 0)
        self._approve_all_btn.setText(
            f"Approve All Pending ({pending})" if pending > 0 else "Approve All Pending"
        )

    def _populate(self, machines):
        self._table.setRowCount(0)
        for m in machines:
            row = self._table.rowCount()
            self._table.insertRow(row)

            status = m.get("status", "unknown")
            reg    = (m.get("registered_at") or "")[:10]

            if status == "approved":
                status_color = _GREEN
            elif status == "pending":
                status_color = _AMBER
            else:
                status_color = _RED

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
                    f = QFont()
                    f.setBold(True)
                    item.setFont(f)
                self._table.setItem(row, col, item)

            # Action buttons
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)
            cell_widget = QWidget()
            cell_widget.setLayout(btn_layout)

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

            self._table.setCellWidget(row, 6, cell_widget)

        self._table.resizeRowsToContents()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _revoke(self, machine_id: str, hostname: str):
        r = QMessageBox.question(
            self, "Revoke Machine",
            f"Revoke access for <b>{hostname or machine_id}</b>?<br><br>"
            "The machine will be blocked on the next app launch.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if r != QMessageBox.Yes:
            return
        self._call("revoke", machine_id)

    def _approve(self, machine_id: str, hostname: str):
        self._call("approve", machine_id)

    def _approve_all_pending(self):
        pending = [m for m in self._machines if m.get("status") == "pending"]
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
        failed = 0
        for m in pending:
            try:
                import requests
                from api_config import API_URL, API_KEY

                tok = requests.post(
                    f"{API_URL}/api/token", json={"api_key": API_KEY}, timeout=5
                ).json().get("token", "")
                resp = requests.post(
                    f"{API_URL}/api/machine/approve/{m['machine_id']}",
                    headers={"Authorization": f"Bearer {tok}"},
                    timeout=5,
                )
                if resp.status_code != 200:
                    failed += 1
            except Exception as exc:
                logger.error("Approve failed for %s: %s", m.get("hostname"), exc)
                failed += 1

        if failed:
            QMessageBox.warning(self, "Partial Success",
                                f"{len(pending) - failed} approved, {failed} failed.")
        self._load()

    def _call(self, action: str, machine_id: str):
        try:
            import requests
            from api_config import API_URL, API_KEY

            tok = requests.post(
                f"{API_URL}/api/token", json={"api_key": API_KEY}, timeout=5
            ).json().get("token", "")
            resp = requests.post(
                f"{API_URL}/api/machine/{action}/{machine_id}",
                headers={"Authorization": f"Bearer {tok}"},
                timeout=5,
            )
            if resp.status_code == 200:
                self._load()
            else:
                QMessageBox.warning(self, "Error",
                                    f"Action failed (HTTP {resp.status_code})")
        except Exception as exc:
            QMessageBox.warning(self, "Error", str(exc))
