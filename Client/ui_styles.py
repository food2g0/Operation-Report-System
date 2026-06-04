from PyQt5.QtWidgets import QFrame, QLabel
from Client.ui_scaling import _sz

__all__ = [
    '_SLATE_50', '_SLATE_100', '_SLATE_200', '_SLATE_300', '_SLATE_400',
    '_SLATE_500', '_SLATE_600', '_SLATE_700', '_SLATE_800', '_SLATE_900',
    '_INDIGO_50', '_INDIGO_100', '_INDIGO_400', '_INDIGO_500', '_INDIGO_600',
    '_INDIGO_700', '_EMERALD_50', '_EMERALD_400', '_EMERALD_500', '_EMERALD_600',
    '_AMBER_400', '_AMBER_500', '_RED_400', '_RED_500', '_WHITE',
    '_BG_APP', '_BG_CARD', '_BG_INPUT', '_BG_RDONLY', '_BG_HEADER', '_BORDER',
    '_TEXT_PRI', '_TEXT_SEC', '_TEXT_MUTED', '_PRIMARY', '_PRIMARY_DK',
    '_PRIMARY_PR', '_SUCCESS', '_SUCCESS_DK', '_build_global_qss'
]

_SLATE_50   = "#F8FAFC"
_SLATE_100  = "#F1F5F9"
_SLATE_200  = "#E2E8F0"
_SLATE_300  = "#CBD5E1"
_SLATE_400  = "#94A3B8"
_SLATE_500  = "#64748B"
_SLATE_600  = "#475569"
_SLATE_700  = "#334155"
_SLATE_800  = "#1E293B"
_SLATE_900  = "#0F172A"

_INDIGO_50  = "#EEF2FF"
_INDIGO_100 = "#E0E7FF"
_INDIGO_400 = "#818CF8"
_INDIGO_500 = "#0C0C0F"
_INDIGO_600 = "#0B0B0C"
_INDIGO_700 = "#111014"

_EMERALD_50  = "#ECFDF5"
_EMERALD_400 = "#34D399"
_EMERALD_500 = "#10B981"
_EMERALD_600 = "#059669"

_AMBER_400  = "#FBBF24"
_AMBER_500  = "#F59E0B"
_RED_400    = "#F87171"
_RED_500    = "#EF4444"
_WHITE      = "#FFFFFF"

_BG_APP     = _SLATE_100
_BG_CARD    = _WHITE
_BG_INPUT   = _WHITE
_BG_RDONLY  = _SLATE_50
_BG_HEADER  = _SLATE_900
_BORDER     = _SLATE_200
_TEXT_PRI   = _SLATE_800
_TEXT_SEC   = _SLATE_500
_TEXT_MUTED = _SLATE_400
_PRIMARY    = _INDIGO_500
_PRIMARY_DK = _INDIGO_600
_PRIMARY_PR = _INDIGO_700
_SUCCESS    = _EMERALD_500
_SUCCESS_DK = _EMERALD_600


def _build_global_qss():
    return f"""

QWidget {{
    background-color: {_BG_APP};
    font-family: 'Segoe UI', 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif;
    font-size: {_sz(13)}px;
    color: {_TEXT_PRI};
}}

QGroupBox {{
    background-color: {_BG_CARD};
    border: 1px solid {_BORDER};
    border-radius: {_sz(8)}px;
    margin-top: {_sz(22)}px;
    padding: {_sz(18)}px {_sz(16)}px {_sz(16)}px {_sz(16)}px;
    font-size: {_sz(11)}px;
    font-weight: 700;
    color: {_TEXT_SEC};
    letter-spacing: 1.2px;
    text-transform: uppercase;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: {_sz(12)}px;
    top: -1px;
    padding: {_sz(2)}px {_sz(8)}px;
    background-color: {_BG_CARD};
    color: {_PRIMARY};
    font-size: {_sz(11)}px;
    font-weight: 800;
    letter-spacing: 1.3px;
    border-radius: 3px;
}}

QLineEdit {{
    background-color: {_BG_INPUT};
    border: 1.5px solid {_BORDER};
    border-radius: {_sz(6)}px;
    padding: {_sz(7)}px {_sz(10)}px;
    font-size: {_sz(14)}px;
    font-weight: 500;
    color: {_TEXT_PRI};
    min-width: {_sz(80)}px;
    min-height: {_sz(34)}px;
    selection-background-color: {_INDIGO_100};
    selection-color: {_PRIMARY_DK};
}}
QLineEdit:focus {{
    border: 2px solid {_PRIMARY};
    background-color: {_INDIGO_50};
    padding: {_sz(6)}px {_sz(9)}px;
}}
QLineEdit:read-only {{
    background-color: {_BG_RDONLY};
    color: {_TEXT_PRI};
    font-weight: 600;
    border-color: {_BORDER};
}}
QLineEdit:disabled {{
    background-color: {_SLATE_100};
    color: {_TEXT_SEC};
    border-color: {_SLATE_200};
}}

QLabel {{
    color: {_TEXT_PRI};
    font-size: {_sz(13)}px;
    font-weight: 500;
    min-width: 0;
    background: transparent;
}}

QPushButton {{
    background-color: {_PRIMARY};
    color: {_WHITE};
    border: none;
    padding: {_sz(8)}px {_sz(18)}px;
    border-radius: {_sz(6)}px;
    font-size: {_sz(12)}px;
    font-weight: 700;
    min-width: {_sz(80)}px;
    letter-spacing: 0.2px;
}}
QPushButton:hover   {{ background-color: {_PRIMARY_DK}; }}
QPushButton:pressed {{ background-color: {_PRIMARY_PR}; }}
QPushButton:disabled {{
    background-color: {_SLATE_200};
    color: {_TEXT_SEC};
}}

QTabWidget::pane {{
    border: 1px solid {_BORDER};
    background-color: {_BG_CARD};
    border-radius: 0 {_sz(8)}px {_sz(8)}px {_sz(8)}px;
    top: -1px;
}}
QTabBar::tab {{
    background-color: {_SLATE_100};
    color: {_TEXT_PRI};
    border: 1px solid {_BORDER};
    border-bottom: none;
    padding: {_sz(10)}px {_sz(24)}px;
    margin-right: 2px;
    border-top-left-radius: {_sz(6)}px;
    border-top-right-radius: {_sz(6)}px;
    font-size: {_sz(13)}px;
    font-weight: 600;
    min-width: {_sz(110)}px;
}}
QTabBar::tab:selected {{
    background-color: {_BG_CARD};
    color: {_PRIMARY};
    font-weight: 700;
    border-bottom: 2px solid {_BG_CARD};
}}
QTabBar::tab:hover:!selected {{
    background-color: {_SLATE_200};
    color: {_TEXT_PRI};
}}

QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: transparent; width: 5px; border-radius: 3px; margin: 2px 0;
}}
QScrollBar::handle:vertical {{
    background: {_SLATE_300}; border-radius: 3px; min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {_SLATE_400}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; border: none; }}
QScrollBar:horizontal {{
    background: transparent; height: 5px; border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {_SLATE_300}; border-radius: 3px;
}}
QScrollBar::handle:horizontal:hover {{ background: {_SLATE_400}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; border: none; }}

QDateEdit {{
    background-color: {_BG_INPUT};
    border: 1.5px solid {_BORDER};
    border-radius: {_sz(6)}px;
    padding: {_sz(7)}px {_sz(10)}px;
    font-size: {_sz(14)}px;
    font-weight: 600;
    color: {_TEXT_PRI};
    min-height: {_sz(34)}px;
}}
QDateEdit:focus {{ border: 2px solid {_PRIMARY}; padding: {_sz(6)}px {_sz(9)}px; }}
QDateEdit::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border: none;
    border-left: 1px solid {_BORDER};
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: {_SLATE_100};
}}
QDateEdit::drop-down:hover {{
    background-color: {_INDIGO_100};
}}
QDateEdit::down-arrow {{
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB4PSIyIiB5PSIyIiB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHJ4PSIyIiBzdHJva2U9IiM0NzU1NjkiIHN0cm9rZS13aWR0aD0iMS41Ii8+PHBhdGggZD0iTTIgNkgxNCIgc3Ryb2tlPSIjNDc1NTY5IiBzdHJva2Utd2lkdGg9IjEuNSIvPjxjaXJjbGUgY3g9IjUiIGN5PSIxMCIgcj0iMSIgZmlsbD0iIzQ3NTU2OSIvPjxjaXJjbGUgY3g9IjgiIGN5PSIxMCIgcj0iMSIgZmlsbD0iIzQ3NTU2OSIvPjxjaXJjbGUgY3g9IjExIiBjeT0iMTAiIHI9IjEiIGZpbGw9IiM0NzU1NjkiLz48L3N2Zz4=);
    width: 16px;
    height: 16px;
}}

QComboBox {{
    background-color: {_BG_INPUT};
    border: 1.5px solid {_BORDER};
    border-radius: {_sz(6)}px;
    padding: {_sz(7)}px {_sz(10)}px;
    font-size: {_sz(14)}px;
    font-weight: 600;
    color: {_TEXT_PRI};
    min-height: {_sz(34)}px;
    min-width: {_sz(120)}px;
}}
QComboBox:focus {{
    border: 2px solid {_PRIMARY};
    background-color: {_INDIGO_50};
}}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox::down-arrow {{
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw2IDZMMTEgMSIgc3Ryb2tlPSIjNjQ3NDhCIiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+PC9zdmc+);
    width: 12px; height: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {_BG_CARD};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    selection-background-color: {_INDIGO_100};
    selection-color: {_PRIMARY_DK};
    padding: 3px;
}}
QComboBox QAbstractItemView::item {{
    padding: {_sz(7)}px {_sz(12)}px;
    border-radius: 3px;
    color: {_TEXT_PRI};
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: {_INDIGO_50};
}}
"""
