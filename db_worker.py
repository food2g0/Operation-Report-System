from PyQt5.QtCore import QRunnable, QObject, pyqtSignal, pyqtSlot, Qt, QThreadPool, QTimer
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PyQt5.QtGui import QFont, QMovie
from typing import Optional, Callable, Any
import traceback
import os


class WorkerSignals(QObject):

    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class DBWorker(QRunnable):

    
    def __init__(self, query: str, params: Optional[tuple] = None, db_manager=None):
        super().__init__()
        self.query = query
        self.params = params
        self.signals = WorkerSignals()
        self._is_cancelled = False
        self.setAutoDelete(True)
        
        if db_manager is None:
            from db_connect_pooled import db_manager as default_db
            self.db_manager = default_db
        else:
            self.db_manager = db_manager
    
    def cancel(self):
        self._is_cancelled = True

    @pyqtSlot()
    def run(self):
        if self._is_cancelled:
            self.signals.finished.emit()
            return

        try:
            result = self.db_manager.execute_query(self.query, self.params)
            if self._is_cancelled:
                self.signals.finished.emit()
                return
            if result is not None:
                self.signals.result.emit(result)
            else:
                self.signals.error.emit("Query returned no results or failed")
        except Exception as e:
            if not self._is_cancelled:
                traceback.print_exc()
                self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


class DBWorkerWithCallback(QRunnable):

    def __init__(self, func: Callable, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._is_cancelled = False
        self.setAutoDelete(True)

    def cancel(self):
        self._is_cancelled = True

    @pyqtSlot()
    def run(self):
        if self._is_cancelled:
            self.signals.finished.emit()
            return
        try:
            result = self.func(*self.args, **self.kwargs)
            if not self._is_cancelled:
                self.signals.result.emit(result)
        except Exception as e:
            if not self._is_cancelled:
                traceback.print_exc()
                self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


def execute_async(query: str, params: Optional[tuple] = None, 
                  on_result: Optional[Callable] = None,
                  on_error: Optional[Callable] = None,
                  on_finished: Optional[Callable] = None,
                  db_manager=None):

    from PyQt5.QtCore import QThreadPool
    
    worker = DBWorker(query, params, db_manager)
    
    if on_result:
        worker.signals.result.connect(on_result)
    if on_error:
        worker.signals.error.connect(on_error)
    if on_finished:
        worker.signals.finished.connect(on_finished)
    
    QThreadPool.globalInstance().start(worker)




class LoadingOverlay(QWidget):


    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("loadingOverlay")
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("""
            #loadingOverlay {
                background-color: rgba(245, 246, 250, 180);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self._label = QLabel(" Loading data…")
        self._label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self._label.setStyleSheet("color: #2c3e50; background: transparent;")
        self._label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._label)

        self.hide()

    def show_overlay(self, message: str = "Loading data…"):
        """Show the overlay, resized to parent."""
        self._label.setText(message)
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.raise_()
        self.show()

    def hide_overlay(self):
        self.hide()

    def resizeEvent(self, event):
        if self.parent():
            self.setGeometry(self.parent().rect())
        super().resizeEvent(event)

def run_query_async(
    parent: QWidget,
    query: str,
    params: Optional[tuple] = None,
    on_result: Optional[Callable] = None,
    on_error: Optional[Callable] = None,
    loading_message: str = "⏳Loading data…",
    db_manager=None,
):

    # Cancel previous in-flight worker to avoid stale results
    prev_worker = getattr(parent, '_active_db_worker', None)
    if prev_worker is not None:
        prev_worker.cancel()

    # Create or reuse overlay
    overlay = getattr(parent, '_loading_overlay', None)
    if overlay is None:
        overlay = LoadingOverlay(parent)
        parent._loading_overlay = overlay
    overlay.show_overlay(loading_message)

    worker = DBWorker(query, params, db_manager)
    parent._active_db_worker = worker

    def _on_result(result):
        overlay.hide_overlay()
        parent._active_db_worker = None
        if on_result:
            on_result(result)

    def _on_error(err):
        overlay.hide_overlay()
        parent._active_db_worker = None
        if on_error:
            on_error(err)

    def _on_finished():
        overlay.hide_overlay()

    worker.signals.result.connect(_on_result)
    worker.signals.error.connect(_on_error)
    worker.signals.finished.connect(_on_finished)

    QThreadPool.globalInstance().start(worker)
    return worker


def run_func_async(
    parent: QWidget,
    func: Callable,
    *args,
    on_result: Optional[Callable] = None,
    on_error: Optional[Callable] = None,
    loading_message: str = "Loading data…",
    **kwargs,
):

    # Cancel previous in-flight worker
    prev_worker = getattr(parent, '_active_db_worker', None)
    if prev_worker is not None:
        prev_worker.cancel()

    overlay = getattr(parent, '_loading_overlay', None)
    if overlay is None:
        overlay = LoadingOverlay(parent)
        parent._loading_overlay = overlay
    overlay.show_overlay(loading_message)

    worker = DBWorkerWithCallback(func, *args, **kwargs)
    parent._active_db_worker = worker

    def _on_result(result):
        overlay.hide_overlay()
        parent._active_db_worker = None
        if on_result:
            on_result(result)

    def _on_error(err):
        overlay.hide_overlay()
        parent._active_db_worker = None
        if on_error:
            on_error(err)

    worker.signals.result.connect(_on_result)
    worker.signals.error.connect(_on_error)
    worker.signals.finished.connect(lambda: overlay.hide_overlay())

    QThreadPool.globalInstance().start(worker)
    return worker
