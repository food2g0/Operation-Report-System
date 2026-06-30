ADMIN_STYLESHEET = """
    /* ── Base ─────────────────────────────────────────────────────────────── */
    QWidget {
        background-color: #F0F2F5;
        font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
        font-size: 12px;
        color: #1A2332;
    }

    /* ── Buttons ──────────────────────────────────────────────────────────── */
    QPushButton {
        background-color: #2563EB;
        color: #FFFFFF;
        border: none;
        padding: 8px 18px;
        border-radius: 7px;
        font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
        font-weight: 600;
        font-size: 12px;
        min-height: 32px;
        letter-spacing: 0.2px;
    }
    QPushButton:hover {
        background-color: #1D4ED8;
    }
    QPushButton:pressed {
        background-color: #1E40AF;
    }
    QPushButton:disabled {
        background-color: #CBD5E1;
        color: #94A3B8;
    }

    QPushButton#saveButton {
        background-color: #16A34A;
        font-size: 13px;
        font-weight: 700;
        padding: 10px 24px;
        min-width: 130px;
        border-radius: 8px;
    }
    QPushButton#saveButton:hover  { background-color: #15803D; }
    QPushButton#saveButton:pressed { background-color: #166534; }

    QPushButton#loadButton {
        background-color: #D97706;
        font-size: 11px;
        font-weight: 600;
        padding: 6px 14px;
    }
    QPushButton#loadButton:hover  { background-color: #B45309; }
    QPushButton#loadButton:pressed { background-color: #92400E; }

    QPushButton#resetButton {
        background-color: #EA580C;
    }
    QPushButton#resetButton:hover  { background-color: #C2410C; }

    QPushButton#exportButton {
        background-color: #059669;
    }
    QPushButton#exportButton:hover  { background-color: #047857; }

    QPushButton#fullBrandReportButton {
        background-color: #7C3AED;
    }
    QPushButton#fullBrandReportButton:hover  { background-color: #6D28D9; }

    /* ── Group Boxes ──────────────────────────────────────────────────────── */
    QGroupBox {
        font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
        font-weight: 700;
        font-size: 11px;
        color: #64748B;
        border: 1.5px solid #D1D5DB;
        border-radius: 10px;
        margin-top: 12px;
        padding-top: 16px;
        background-color: #FFFFFF;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        top: -1px;
        padding: 2px 10px;
        color: #2563EB;
        font-weight: 700;
        font-size: 11px;
        background-color: #FFFFFF;
        border-radius: 4px;
    }

    /* ── Labels ───────────────────────────────────────────────────────────── */
    QLabel {
        color: #1E293B;
        font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
        font-size: 12px;
        font-weight: 500;
        background: transparent;
    }
    QLabel[class="header"] {
        font-weight: 700;
        font-size: 14px;
        color: #0F172A;
    }
    QLabel[class="section"] {
        font-weight: 700;
        font-size: 13px;
        color: #1E293B;
        background-color: #EFF6FF;
        padding: 5px 10px;
        border-radius: 5px;
        border-left: 3px solid #2563EB;
    }

    /* ── Input Fields ─────────────────────────────────────────────────────── */
    QLineEdit {
        border: 1.5px solid #CBD5E1;
        border-radius: 6px;
        padding: 6px 10px;
        font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
        font-size: 12px;
        font-weight: 500;
        color: #0F172A;
        background-color: #FFFFFF;
        min-height: 24px;
        selection-background-color: #DBEAFE;
        selection-color: #1E3A8A;
    }
    QLineEdit:focus {
        border: 2px solid #2563EB;
        background-color: #EFF6FF;
        padding: 5px 9px;
    }
    QLineEdit:read-only {
        background-color: #F8FAFC;
        border: 1.5px solid #E2E8F0;
        color: #334155;
        font-weight: 600;
    }
    QLineEdit:disabled {
        background-color: #F1F5F9;
        color: #94A3B8;
        border-color: #E2E8F0;
    }
    QLineEdit[class="money"] {
        font-weight: 700;
        text-align: right;
        color: #0F172A;
        font-size: 13px;
    }
    QLineEdit[class="result"] {
        background-color: #FEFCE8;
        border: 2px solid #EAB308;
        font-weight: 700;
        font-size: 13px;
        color: #713F12;
    }

    /* ── Dropdowns ────────────────────────────────────────────────────────── */
    QComboBox {
        border: 1.5px solid #CBD5E1;
        border-radius: 6px;
        padding: 6px 10px;
        background-color: #FFFFFF;
        font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
        font-size: 12px;
        font-weight: 500;
        color: #0F172A;
        min-width: 120px;
        min-height: 28px;
    }
    QComboBox:focus {
        border: 2px solid #2563EB;
        background-color: #EFF6FF;
    }
    QComboBox::drop-down {
        border: none;
        width: 24px;
    }
    QComboBox::down-arrow {
        width: 12px;
        height: 12px;
    }
    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        selection-background-color: #DBEAFE;
        selection-color: #1E40AF;
        padding: 3px;
        font-size: 12px;
    }

    /* ── Date Edit ────────────────────────────────────────────────────────── */
    QDateEdit {
        border: 1.5px solid #CBD5E1;
        border-radius: 6px;
        padding: 6px 30px 6px 10px;
        background-color: #FFFFFF;
        font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
        font-size: 12px;
        font-weight: 600;
        color: #0F172A;
        min-height: 28px;
        min-width: 135px;
    }
    QDateEdit:focus {
        border: 2px solid #2563EB;
        background-color: #EFF6FF;
    }
    QDateEdit::drop-down {
        subcontrol-origin: border;
        subcontrol-position: center right;
        width: 30px;
        border-left: 1.5px solid #CBD5E1;
        background-color: #F1F5F9;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
    }
    QDateEdit::drop-down:hover {
        background-color: #DBEAFE;
    }
    QDateEdit::down-arrow {
        width: 11px;
        height: 11px;
    }

    /* ── Calendar ─────────────────────────────────────────────────────────── */
    QCalendarWidget {
        min-width: 340px;
        min-height: 280px;
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
    }
    QCalendarWidget QWidget#qt_calendar_navigationbar {
        background-color: #1E293B;
        min-height: 44px;
        padding: 4px 8px;
        border-radius: 6px 6px 0 0;
    }
    QCalendarWidget QToolButton {
        color: #E2E8F0;
        font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
        font-size: 13px;
        font-weight: 600;
        background-color: transparent;
        padding: 6px 10px;
        border-radius: 5px;
        margin: 2px;
    }
    QCalendarWidget QToolButton:hover {
        background-color: #2563EB;
        color: #FFFFFF;
    }
    QCalendarWidget QToolButton:pressed {
        background-color: #1D4ED8;
        color: #FFFFFF;
    }
    QCalendarWidget QSpinBox {
        color: #0F172A;
        background-color: #F8FAFC;
        font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
        font-size: 13px;
        font-weight: 600;
        border: 1px solid #CBD5E1;
        border-radius: 4px;
        padding: 4px 8px;
        selection-background-color: #2563EB;
        selection-color: #FFFFFF;
    }
    QCalendarWidget QAbstractItemView {
        background: #FFFFFF;
        selection-background-color: #2563EB;
        selection-color: #FFFFFF;
        font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
        font-size: 12px;
        alternate-background-color: #F8FAFC;
    }
    QCalendarWidget QAbstractItemView::item {
        padding: 6px;
        border-radius: 4px;
        color: #1E293B;
    }
    QCalendarWidget QAbstractItemView::item:selected {
        background-color: #2563EB;
        color: #FFFFFF;
        font-weight: 700;
    }
    QCalendarWidget QAbstractItemView:disabled {
        color: #CBD5E1;
    }

    /* ── Scroll Area ──────────────────────────────────────────────────────── */
    QScrollArea {
        border: none;
        background-color: transparent;
    }
    QScrollBar:vertical {
        background: transparent;
        width: 6px;
        border-radius: 3px;
        margin: 2px 0;
    }
    QScrollBar::handle:vertical {
        background: #CBD5E1;
        border-radius: 3px;
        min-height: 28px;
    }
    QScrollBar::handle:vertical:hover { background: #94A3B8; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; border: none; }
    QScrollBar:horizontal {
        background: transparent;
        height: 6px;
        border-radius: 3px;
    }
    QScrollBar::handle:horizontal {
        background: #CBD5E1;
        border-radius: 3px;
    }
    QScrollBar::handle:horizontal:hover { background: #94A3B8; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; border: none; }

    /* ── Tables ───────────────────────────────────────────────────────────── */
    QTableWidget {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        gridline-color: #F1F5F9;
        font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
        font-size: 12px;
        color: #1E293B;
        alternate-background-color: #F8FAFC;
        selection-background-color: #DBEAFE;
        selection-color: #1E40AF;
    }
    QTableWidget::item {
        padding: 6px 10px;
    }
    QTableWidget::item:selected {
        background-color: #DBEAFE;
        color: #1E40AF;
    }
    QHeaderView::section {
        background-color: #1E293B;
        color: #F1F5F9;
        font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
        font-weight: 700;
        font-size: 11px;
        padding: 8px 10px;
        border: none;
        border-right: 1px solid #334155;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    QHeaderView::section:first {
        border-top-left-radius: 7px;
    }
    QHeaderView::section:last {
        border-right: none;
        border-top-right-radius: 7px;
    }

    /* ── Navigation Bar ───────────────────────────────────────────────────── */
    QFrame#navBar {
        background-color: #0F172A;
        border-radius: 0px;
        margin-bottom: 0px;
        padding: 0px;
    }
    QFrame#navBar QPushButton {
        background-color: transparent;
        border: none;
        border-bottom: 3px solid transparent;
        color: #94A3B8;
        font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
        font-size: 11px;
        font-weight: 600;
        padding: 11px 8px;
        border-radius: 0px;
        letter-spacing: 0.3px;
    }
    QFrame#navBar QPushButton:hover {
        background-color: rgba(37, 99, 235, 0.15);
        color: #E2E8F0;
        border-bottom: 3px solid #3B82F6;
    }
    QFrame#navBar QPushButton:checked {
        background-color: rgba(37, 99, 235, 0.22);
        color: #FFFFFF;
        border-bottom: 3px solid #2563EB;
    }

    /* ── Tab Widget ───────────────────────────────────────────────────────── */
    QTabWidget::pane {
        border: 1.5px solid #E2E8F0;
        background-color: #FFFFFF;
        border-radius: 0 8px 8px 8px;
        top: -1px;
    }
    QTabBar::tab {
        background-color: #F1F5F9;
        color: #64748B;
        border: 1px solid #E2E8F0;
        border-bottom: none;
        padding: 9px 20px;
        margin-right: 2px;
        border-top-left-radius: 7px;
        border-top-right-radius: 7px;
        font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
        font-size: 12px;
        font-weight: 600;
        min-width: 100px;
    }
    QTabBar::tab:selected {
        background-color: #FFFFFF;
        color: #2563EB;
        font-weight: 700;
        border-bottom: 2px solid #FFFFFF;
    }
    QTabBar::tab:hover:!selected {
        background-color: #E2E8F0;
        color: #1E293B;
    }
"""
