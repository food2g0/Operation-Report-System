"""
Asynchronous Database Worker for PyQt5
Prevents UI blocking during database operations

Usage Example:
    from db_worker import DBWorker
    
    def on_data_ready(result):
        if result:
            # Update UI with result
            self.populate_table(result)
    
    def on_error(error_msg):
        QMessageBox.warning(self, "Error", error_msg)
    
    # Execute query in background thread
    worker = DBWorker(
        query="SELECT * FROM daily_reports WHERE date = %s",
        params=("2026-02-16",)
    )
    worker.signals.result.connect(on_data_ready)
    worker.signals.error.connect(on_error)
    worker.signals.finished.connect(lambda: print("Query completed"))
    
    # Start the worker (uses global QThreadPool)
    from PyQt5.QtCore import QThreadPool
    QThreadPool.globalInstance().start(worker)
"""
from PyQt5.QtCore import QRunnable, QObject, pyqtSignal, pyqtSlot
from typing import Optional, Callable, Any
import traceback


class WorkerSignals(QObject):
    """
    Signals for DBWorker
    """
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class DBWorker(QRunnable):
    """
    Worker thread for database operations
    Prevents UI blocking during long-running queries
    """
    
    def __init__(self, query: str, params: Optional[tuple] = None, db_manager=None):
        super().__init__()
        self.query = query
        self.params = params
        self.signals = WorkerSignals()
        
        # Import db_manager if not provided
        if db_manager is None:
            from db_connect import db_manager as default_db
            self.db_manager = default_db
        else:
            self.db_manager = db_manager
    
    @pyqtSlot()
    def run(self):
        """
        Execute the query in a background thread
        """
        try:
            result = self.db_manager.execute_query(self.query, self.params)
            if result is not None:
                self.signals.result.emit(result)
            else:
                self.signals.error.emit("Query returned no results or failed")
        except Exception as e:
            traceback.print_exc()
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


class DBWorkerWithCallback(QRunnable):
    """
    Database worker that executes a custom function in background
    Useful for complex operations beyond simple queries
    
    Example:
        def complex_operation():
            # Do multiple queries, calculations, etc.
            data = db_manager.execute_query("SELECT ...")
            processed = process_data(data)
            return processed
        
        worker = DBWorkerWithCallback(complex_operation)
        worker.signals.result.connect(on_result)
        QThreadPool.globalInstance().start(worker)
    """
    
    def __init__(self, func: Callable, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
    
    @pyqtSlot()
    def run(self):
        """Execute the function in background thread"""
        try:
            result = self.func(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            traceback.print_exc()
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


# Convenience function for simple async queries
def execute_async(query: str, params: Optional[tuple] = None, 
                  on_result: Optional[Callable] = None,
                  on_error: Optional[Callable] = None,
                  on_finished: Optional[Callable] = None,
                  db_manager=None):
    """
    Execute a database query asynchronously
    
    Args:
        query: SQL query string
        params: Query parameters
        on_result: Callback function for results (receives result data)
        on_error: Callback function for errors (receives error message)
        on_finished: Callback function called when complete (no args)
        db_manager: Optional db_manager instance (uses default if None)
    
    Example:
        def handle_data(data):
            print(f"Got {len(data)} rows")
        
        execute_async(
            "SELECT * FROM daily_reports WHERE date > %s",
            params=("2026-01-01",),
            on_result=handle_data,
            on_error=lambda err: print(f"Error: {err}")
        )
    """
    from PyQt5.QtCore import QThreadPool
    
    worker = DBWorker(query, params, db_manager)
    
    if on_result:
        worker.signals.result.connect(on_result)
    if on_error:
        worker.signals.error.connect(on_error)
    if on_finished:
        worker.signals.finished.connect(on_finished)
    
    QThreadPool.globalInstance().start(worker)
