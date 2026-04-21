"""
Performance Monitoring Utilities
Track query execution times and identify bottlenecks

Usage:
    from performance_utils import query_timer, PerformanceMonitor
    
    # Decorate functions to track execution time
    @query_timer
    def slow_operation():
        result = db_manager.execute_query("SELECT * FROM large_table")
        return result
    
    # Or use context manager
    with PerformanceMonitor("Loading dashboard data"):
        data = load_all_data()
"""
import time
import logging
from functools import wraps
from typing import Callable, Any
from datetime import datetime

# Setup performance logger
perf_logger = logging.getLogger("Performance")
perf_logger.setLevel(logging.INFO)
if not perf_logger.handlers:
    handler = logging.FileHandler("performance.log")
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    perf_logger.addHandler(handler)


def query_timer(func: Callable) -> Callable:
    """
    Decorator to measure function execution time
    Logs slow operations (> 1 second) automatically
    
    Example:
        @query_timer
        def load_reports(date):
            return db_manager.execute_query("SELECT * FROM daily_reports WHERE date = %s", (date,))
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        # Log slow operations
        if elapsed > 1.0:
            perf_logger.warning(f"SLOW: {func.__name__} took {elapsed:.2f}s")
        else:
            perf_logger.info(f"{func.__name__} took {elapsed:.3f}s")
        
        return result
    return wrapper


class PerformanceMonitor:
    """
    Context manager for monitoring code block performance
    
    Example:
        with PerformanceMonitor("Database batch insert"):
            for row in rows:
                db_manager.execute_query(insert_query, row)
    """
    
    def __init__(self, operation_name: str, threshold_seconds: float = 1.0):
        self.operation_name = operation_name
        self.threshold = threshold_seconds
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        
        if elapsed > self.threshold:
            perf_logger.warning(f"SLOW: {self.operation_name} took {elapsed:.2f}s")
        else:
            perf_logger.info(f"{self.operation_name} took {elapsed:.3f}s")


class QueryProfiler:
    """
    Collect statistics about all queries executed during profiling session
    
    Example:
        profiler = QueryProfiler()
        profiler.start()
        # ... run your code ...
        profiler.stop()
        print(profiler.get_report())
    """
    
    def __init__(self):
        self.queries = []
        self.is_profiling = False
        self.original_execute = None
    
    def start(self):
        """Start profiling database queries"""
        from db_connect_pooled import db_manager
        self.is_profiling = True
        self.queries = []
        
        # Monkey-patch execute_query to track calls
        self.original_execute = db_manager.execute_query
        
        def tracked_execute(query, params=None):
            start = time.time()
            result = self.original_execute(query, params)
            elapsed = time.time() - start
            
            self.queries.append({
                'query': query[:100],  # First 100 chars
                'params': str(params)[:50] if params else None,
                'duration': elapsed,
                'timestamp': datetime.now()
            })
            
            return result
        
        db_manager.execute_query = tracked_execute
        perf_logger.info("Query profiling started")
    
    def stop(self):
        """Stop profiling and restore original execute_query"""
        if self.original_execute:
            from db_connect_pooled import db_manager
            db_manager.execute_query = self.original_execute
            self.original_execute = None
        
        self.is_profiling = False
        perf_logger.info("Query profiling stopped")
    
    def get_report(self) -> str:
        """Generate a performance report"""
        if not self.queries:
            return "No queries recorded"
        
        total_time = sum(q['duration'] for q in self.queries)
        avg_time = total_time / len(self.queries)
        slowest = max(self.queries, key=lambda q: q['duration'])
        
        report = f"""
Performance Report
==================
Total queries: {len(self.queries)}
Total time: {total_time:.2f}s
Average time per query: {avg_time:.3f}s
Slowest query: {slowest['duration']:.2f}s
  Query: {slowest['query']}

Queries by duration:
"""
        
        # Sort by duration (slowest first)
        sorted_queries = sorted(self.queries, key=lambda q: q['duration'], reverse=True)
        for i, q in enumerate(sorted_queries[:10], 1):
            report += f"\n{i}. {q['duration']:.3f}s - {q['query']}"
        
        return report
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# Example usage and testing
if __name__ == "__main__":
    @query_timer
    def example_slow_function():
        time.sleep(1.5)
        return "Done"
    
    @query_timer
    def example_fast_function():
        time.sleep(0.1)
        return "Done"
    
    print("Testing performance decorators...")
    example_slow_function()
    example_fast_function()
    
    with PerformanceMonitor("Test operation"):
        time.sleep(0.5)
    
    print("\nCheck performance.log for results")
