ADMIN_STYLESHEET = """
    QWidget {
        background-color: #f5f6fa;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 12px;
    }

    /* Navigation Buttons */
    QPushButton {
        background-color: #3498db;
        color: black;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 12px;
        min-height: 30px;
    }

    QPushButton:hover {
        background-color: #2980b9;
    }

    QPushButton:pressed {
        background-color: #21618c;
    }

    QPushButton#saveButton {
        background-color: #27ae60;
        font-size: 13px;
        padding: 10px 20px;
        min-width: 120px;
    }

    QPushButton#saveButton:hover {
        background-color: #219a52;
    }

    QPushButton#loadButton {
        background-color: #f39c12;
        font-size: 11px;
        padding: 6px 12px;
    }

    QPushButton#loadButton:hover {
        background-color: #e67e22;
    }

    /* Group Boxes */
    QGroupBox {
        font-weight: bold;
        font-size: 13px;
        color: #2c3e50;
        border: 2px solid #bdc3c7;
        border-radius: 8px;
        margin-top: 10px;
        padding-top: 15px;
        background-color: white;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 8px 0 8px;
        color: #2c3e50;
        font-weight: bold;
        font-size: 14px;
        background-color: white;
    }

    /* Labels */
    QLabel {
        color: #2c3e50;
        font-size: 11px;
        font-weight: bold;
    }

    QLabel[class="header"] {
        font-weight: bold;
        font-size: 13px;
        color: #2c3e50;
    }

    QLabel[class="section"] {
        font-weight: bold;
        font-size: 14px;
        color: #34495e;
        background-color: #ecf0f1;
        padding: 5px;
        border-radius: 4px;
    }

    /* Input Fields */
    QLineEdit {
        border: 1px solid #bdc3c7;
        border-radius: 4px;
        padding: 5px 8px;
        font-size: 11px;
        background-color: white;
        min-height: 20px;
    }

    QLineEdit:focus {
        border: 2px solid #3498db;
    }

    QLineEdit[readOnly="true"] {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        font-weight: bold;
        color: #495057;
    }

    QLineEdit[class="money"] {
        font-weight: bold;
        text-align: right;
        color: #000000;
        font-size: 12px;
    }

    QLineEdit[class="result"] {
        background-color: #fff3cd;
        border: 2px solid #ffeaa7;
        font-weight: bold;
        font-size: 12px;
        color: #000000;
    }

    /* Dropdowns */
    QComboBox {
        border: 1px solid #bdc3c7;
        border-radius: 4px;
        padding: 5px 8px;
        background-color: white;
        font-size: 11px;
        min-width: 120px;
        min-height: 25px;
    }

    QComboBox:focus {
        border: 2px solid #3498db;
    }

    QComboBox::drop-down {
        border: none;
        width: 20px;
    }

    QComboBox::down-arrow {
        width: 12px;
        height: 12px;
    }

    /* Date Edit */
    QDateEdit {
        border: 1px solid #bdc3c7;
        border-radius: 4px;
        padding: 5px 28px 5px 8px;
        background-color: white;
        font-size: 11px;
        min-height: 25px;
        min-width: 130px;
    }

    QDateEdit:focus {
        border: 2px solid #3498db;
    }

    QDateEdit::drop-down {
        subcontrol-origin: border;
        subcontrol-position: center right;
        width: 28px;
        border-left: 1px solid #bdc3c7;
        background-color: #ecf0f1;
        border-top-right-radius: 4px;
        border-bottom-right-radius: 4px;
    }

    QDateEdit::drop-down:hover {
        background-color: #d5dbdb;
    }

    QDateEdit::down-arrow {
        width: 10px;
        height: 10px;
    }

    /* Calendar Popup — Standardized */
    QCalendarWidget {
        min-width: 340px;
        min-height: 280px;
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 6px;
    }

    QCalendarWidget QWidget#qt_calendar_navigationbar {
        background-color: #343a40;
        min-height: 42px;
        padding: 4px 6px;
        border-radius: 4px 4px 0 0;
    }

    QCalendarWidget QToolButton {
        color: #ecf0f1;
        font-size: 14px;
        font-weight: bold;
        background-color: transparent;
        padding: 6px 10px;
        border-radius: 4px;
        margin: 2px;
    }

    QCalendarWidget QToolButton:hover {
        background-color: #007bff;
        color: white;
    }

    QCalendarWidget QToolButton:pressed {
        background-color: #0056b3;
        color: white;
    }

    QCalendarWidget QSpinBox {
        color: #2c3e50;
        background-color: #ecf0f1;
        font-size: 13px;
        font-weight: bold;
        border: 1px solid #bdc3c7;
        border-radius: 4px;
        padding: 4px 8px;
        selection-background-color: #007bff;
        selection-color: white;
    }

    QCalendarWidget QAbstractItemView {
        background: white;
        selection-background-color: #007bff;
        selection-color: white;
        font-size: 12px;
        alternate-background-color: #f8f9fa;
    }

    QCalendarWidget QAbstractItemView::item {
        padding: 6px;
        border-radius: 4px;
    }

    QCalendarWidget QAbstractItemView::item:alternate {
        background-color: #f8f9fa;
    }

    QCalendarWidget QAbstractItemView::item:selected {
        background-color: #007bff;
        color: white;
        font-weight: bold;
    }

    QCalendarWidget QAbstractItemView:disabled {
        color: #bdc3c7;
    }

    /* Scroll Area */
    QScrollArea {
        border: none;
        background-color: transparent;
    }

    /* Navigation Bar */
    QFrame#navBar {
        background-color: #2c3e50;
        border-radius: 0px;
        margin-bottom: 0px;
        padding: 0px;
    }

    QFrame#navBar QPushButton {
        background-color: transparent;
        border: none;
        border-bottom: 3px solid transparent;
        color: #bdc3c7;
        font-size: 11px;
        font-weight: bold;
        padding: 10px 6px;
        border-radius: 0px;
    }

    QFrame#navBar QPushButton:hover {
        background-color: rgba(52, 152, 219, 0.15);
        color: #ecf0f1;
        border-bottom: 3px solid #3498db;
    }

    QFrame#navBar QPushButton:checked {
        background-color: rgba(52, 152, 219, 0.25);
        color: #ffffff;
        border-bottom: 3px solid #3498db;
    }
"""
