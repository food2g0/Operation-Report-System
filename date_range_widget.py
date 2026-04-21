
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QDateEdit, QLabel
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont
import calendar


_DATEEDIT_STYLE = (
    "QDateEdit{padding:8px;border:2px solid #dee2e6;border-radius:6px;"
    "background:white;font-size:13px;}"
    "QDateEdit:focus{border-color:#007bff;}"
)

_COMBO_STYLE = (
    "QComboBox{padding:8px;border:2px solid #dee2e6;border-radius:6px;"
    "background:white;font-size:13px;}"
    "QComboBox:focus{border-color:#007bff;}"
    "QComboBox::drop-down{width:28px;}"
)

_MODE_STYLE = (
    "QComboBox{padding:6px 10px;border:2px solid #17a2b8;border-radius:6px;"
    "background:#e8f4f8;font-size:12px;font-weight:bold;color:#0c5460;}"
    "QComboBox:focus{border-color:#007bff;}"
    "QComboBox::drop-down{width:24px;}"
)


class DateRangeWidget(QWidget):
    dateRangeChanged = pyqtSignal()  

    def __init__(self, parent=None):
        super().__init__(parent)
        self._building = True
        self._init_ui()
        self._building = False

    def _init_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Single Date", "single")
        self.mode_combo.addItem("Date Range", "range")
        self.mode_combo.addItem("Monthly", "monthly")
        self.mode_combo.setMinimumHeight(38)
        self.mode_combo.setMinimumWidth(120)
        self.mode_combo.setStyleSheet(_MODE_STYLE)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        lay.addWidget(self.mode_combo)

        self.lbl_date = self._bold_label("Date:")
        lay.addWidget(self.lbl_date)
        self.date_single = self._make_date_edit()
        self.date_single.dateChanged.connect(self._emit)
        lay.addWidget(self.date_single)

        self.lbl_from = self._bold_label("From:")
        lay.addWidget(self.lbl_from)
        self.date_from = self._make_date_edit()
        self.date_from.dateChanged.connect(self._on_from_changed)
        lay.addWidget(self.date_from)

        self.lbl_to = self._bold_label("To:")
        lay.addWidget(self.lbl_to)
        self.date_to = self._make_date_edit()
        self.date_to.dateChanged.connect(self._emit)
        lay.addWidget(self.date_to)

        self.lbl_month = self._bold_label("Month:")
        lay.addWidget(self.lbl_month)
        self.month_combo = QComboBox()
        self.month_combo.setMinimumHeight(38)
        self.month_combo.setMinimumWidth(120)
        self.month_combo.setStyleSheet(_COMBO_STYLE)
        for i in range(1, 13):
            self.month_combo.addItem(calendar.month_name[i], i)
        self.month_combo.setCurrentIndex(QDate.currentDate().month() - 1)
        self.month_combo.currentIndexChanged.connect(self._on_month_year_changed)
        lay.addWidget(self.month_combo)

        self.lbl_year = self._bold_label("Year:")
        lay.addWidget(self.lbl_year)
        self.year_combo = QComboBox()
        self.year_combo.setMinimumHeight(38)
        self.year_combo.setMinimumWidth(90)
        self.year_combo.setStyleSheet(_COMBO_STYLE)
        cur_year = QDate.currentDate().year()
        for y in range(cur_year - 5, cur_year + 2):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(cur_year))
        self.year_combo.currentIndexChanged.connect(self._on_month_year_changed)
        lay.addWidget(self.year_combo)

        self._apply_mode("single")

  
    def get_date_range(self):

        mode = self.mode_combo.currentData()
        if mode == "single":
            d = self.date_single.date().toString("yyyy-MM-dd")
            return d, d
        elif mode == "range":
            return (
                self.date_from.date().toString("yyyy-MM-dd"),
                self.date_to.date().toString("yyyy-MM-dd"),
            )
        else: 
            m = self.month_combo.currentData()
            y = self.year_combo.currentData()
            if m is None or y is None:
                d = self.date_single.date().toString("yyyy-MM-dd")
                return d, d
            first = QDate(y, m, 1)
            last = QDate(y, m, calendar.monthrange(y, m)[1])
            return first.toString("yyyy-MM-dd"), last.toString("yyyy-MM-dd")

    def is_range_mode(self):
  
        return self.mode_combo.currentData() != "single"

    def get_single_date_str(self):

        return self.date_single.date().toString("yyyy-MM-dd")

    def date(self):

        return self.date_single.date()


    def _on_mode_changed(self, _idx):
        mode = self.mode_combo.currentData()
        self._apply_mode(mode)
        if not self._building:
            self._emit()

    def _on_from_changed(self, new_date):

        if self.date_to.date() < new_date:
            self.date_to.blockSignals(True)
            self.date_to.setDate(new_date)
            self.date_to.blockSignals(False)
        self._emit()

    def _on_month_year_changed(self, _idx):
        if not self._building:
            self._emit()

    def _emit(self, *_args):
        if not self._building:
            self.dateRangeChanged.emit()


    def _apply_mode(self, mode):
        is_single = mode == "single"
        is_range = mode == "range"
        is_month = mode == "monthly"

        self.lbl_date.setVisible(is_single)
        self.date_single.setVisible(is_single)

        self.lbl_from.setVisible(is_range)
        self.date_from.setVisible(is_range)
        self.lbl_to.setVisible(is_range)
        self.date_to.setVisible(is_range)

        self.lbl_month.setVisible(is_month)
        self.month_combo.setVisible(is_month)
        self.lbl_year.setVisible(is_month)
        self.year_combo.setVisible(is_month)


    @staticmethod
    def _bold_label(text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Arial", 11, QFont.Bold))
        return lbl

    @staticmethod
    def _make_date_edit():
        de = QDateEdit(calendarPopup=True)
        de.setDate(QDate.currentDate())
        de.setDisplayFormat("yyyy-MM-dd")
        de.setMinimumHeight(38)
        de.setMinimumWidth(150)
        de.setStyleSheet(_DATEEDIT_STYLE)
        return de
