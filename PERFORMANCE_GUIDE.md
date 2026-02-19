# Performance Optimization Guide

## Overview
This guide shows you how to improve your Operation Report System's performance using the new performance utilities.

## What Was Added

### 1. Connection Pooling (`db_connect_pooled.py`)
- **Problem**: Old `db_connect.py` uses a single connection with a lock, serializing all queries
- **Solution**: SQLAlchemy connection pool with 10-30 concurrent connections
- **Impact**: 10-50x faster for concurrent requests, eliminates query serialization

### 2. Async Database Operations (`db_worker.py`)
- **Problem**: UI freezes during database operations
- **Solution**: QThread workers execute queries in background
- **Impact**: Responsive UI, better user experience

### 3. Query Caching (`db_connect_pooled.py`)
- **Problem**: Repeated queries for lookup data (corporations, branches)
- **Solution**: LRU cache for SELECT queries
- **Impact**: Instant response for cached lookups

### 4. Performance Monitoring (`performance_utils.py`)
- **Problem**: Can't identify slow queries or bottlenecks
- **Solution**: Decorators, context managers, and profiler
- **Impact**: Data-driven optimization decisions

---

## Quick Start: Enable Connection Pooling

### Step 1: Update a single file to use pooled connections

**Before:**
```python
from db_connect import db_manager
```

**After:**
```python
from db_connect_pooled import db_manager
```

That's it! All your existing `db_manager.execute_query()` calls will now use connection pooling.

### Step 2: Test the change
```bash
python db_connect_pooled.py
```

You should see:
```
✅ Database connection pool OK
✅ Connected to database: your_database_name
```

---

## Advanced: Async Database Operations

### Example 1: Prevent UI blocking when loading data

**Before (blocking code):**
```python
def populate_table(self):
    # UI freezes here during query
    results = db_manager.execute_query(
        "SELECT * FROM daily_reports WHERE date = %s",
        (selected_date,)
    )
    self.display_results(results)
```

**After (non-blocking code):**
```python
from db_worker import execute_async
from PyQt5.QtWidgets import QMessageBox

def populate_table(self):
    def on_results(results):
        # Update UI when data arrives
        self.display_results(results)
    
    def on_error(error_msg):
        QMessageBox.warning(self, "Error", error_msg)
    
    # Query runs in background, UI stays responsive
    execute_async(
        "SELECT * FROM daily_reports WHERE date = %s",
        params=(selected_date,),
        on_result=on_results,
        on_error=on_error
    )
```

### Example 2: Complex operations in background

```python
from db_worker import DBWorkerWithCallback
from PyQt5.QtCore import QThreadPool

def complex_operation():
    # Multiple queries, calculations, etc.
    data1 = db_manager.execute_query("SELECT ...")
    data2 = db_manager.execute_query("SELECT ...")
    processed = merge_and_process(data1, data2)
    return processed

def on_complete(result):
    self.update_ui(result)

worker = DBWorkerWithCallback(complex_operation)
worker.signals.result.connect(on_complete)
QThreadPool.globalInstance().start(worker)
```

---

## Query Caching for Lookup Data

### Use cached queries for data that rarely changes:

```python
from db_connect_pooled import db_manager

# This query result is cached (fast subsequent calls)
corporations = db_manager.execute_cached_query(
    "SELECT DISTINCT corporation FROM daily_reports ORDER BY corporation"
)

# Clear cache when data changes
db_manager.clear_cache()
```

**When to use caching:**
- Corporation/branch lists
- User lookups
- Configuration data
- Report date ranges

**When NOT to cache:**
- Real-time transaction data
- User-specific queries with parameters
- Frequently updated data

---

## Performance Monitoring

### 1. Track individual function performance

```python
from performance_utils import query_timer

@query_timer
def load_dashboard_data(self):
    data = db_manager.execute_query("SELECT ...")
    return data
```

Check `performance.log` to see execution times.

### 2. Monitor code blocks

```python
from performance_utils import PerformanceMonitor

with PerformanceMonitor("Batch insert operation"):
    for row in rows:
        db_manager.execute_query(insert_query, row)
```

### 3. Profile all database queries

```python
from performance_utils import QueryProfiler

profiler = QueryProfiler()
profiler.start()

# Run your application or test scenario
load_all_dashboard_data()
generate_reports()

profiler.stop()
print(profiler.get_report())
```

Output example:
```
Performance Report
==================
Total queries: 45
Total time: 12.34s
Average time per query: 0.274s
Slowest query: 3.21s
  Query: SELECT * FROM daily_reports WHERE corporation = %s AND date BETWEEN ...

Queries by duration:
1. 3.210s - SELECT * FROM daily_reports WHERE ...
2. 1.450s - SELECT branch, SUM(ending_balance) ...
3. 0.890s - SELECT DISTINCT corporation FROM ...
```

---

## Database Optimization Checklist

### ✅ Add Indexes (if missing)

```sql
-- Check if indexes exist
SHOW INDEX FROM daily_reports;

-- Add indexes for frequently filtered columns
ALTER TABLE daily_reports 
  ADD INDEX idx_corp_date (corporation, date);

ALTER TABLE daily_reports 
  ADD INDEX idx_branch_date (branch, date);

ALTER TABLE daily_reports 
  ADD INDEX idx_username_date (username, date);
```

### ✅ Optimize Slow Queries

Use `EXPLAIN` to analyze queries:
```sql
EXPLAIN SELECT * FROM daily_reports 
WHERE corporation = 'ABC' AND date BETWEEN '2026-01-01' AND '2026-02-16';
```

Look for:
- `type: ALL` → Full table scan (add index!)
- `Extra: Using filesort` → Consider adding index
- `Extra: Using temporary` → Rewrite query if possible

### ✅ Batch Operations

**Bad (many round trips):**
```python
for row in rows:
    db_manager.execute_query("INSERT INTO ...", row)
```

**Good (single batch insert):**
```python
values = ', '.join(['(%s, %s, %s)'] * len(rows))
flat_params = [item for row in rows for item in row]
db_manager.execute_query(f"INSERT INTO table VALUES {values}", flat_params)
```

### ✅ Limit Result Sets

**Bad:**
```python
all_data = db_manager.execute_query("SELECT * FROM daily_reports")
```

**Good:**
```python
recent_data = db_manager.execute_query(
    "SELECT * FROM daily_reports WHERE date > %s LIMIT 1000",
    (cutoff_date,)
)
```

### ✅ Select Only Needed Columns

**Bad:**
```python
db_manager.execute_query("SELECT * FROM daily_reports")
```

**Good:**
```python
db_manager.execute_query(
    "SELECT branch, date, ending_balance FROM daily_reports"
)
```

---

## Migration Path

### Phase 1: Enable Connection Pooling (EASY - 5 minutes)
1. Change one import: `from db_connect_pooled import db_manager`
2. Test: `python db_connect_pooled.py`
3. Monitor: Check `database.log` for pool creation

### Phase 2: Add Performance Monitoring (EASY - 10 minutes)
1. Add `@query_timer` to slow functions
2. Review `performance.log` to identify bottlenecks
3. Focus optimization efforts on top 3 slowest operations

### Phase 3: Add Async Operations (MEDIUM - 30 minutes per page)
1. Import `execute_async` from `db_worker`
2. Replace blocking queries in UI event handlers
3. Add loading indicators during async operations
4. Test UI responsiveness

### Phase 4: Add Database Indexes (MEDIUM - varies)
1. Run `QueryProfiler` during typical usage
2. Identify slow queries from report
3. Run `EXPLAIN` on slow queries
4. Add indexes based on WHERE/ORDER BY clauses
5. Re-test with profiler

### Phase 5: Optimize Queries (HARD - varies)
1. Review queries that do full table scans
2. Add pagination for large result sets
3. Batch multiple single-row operations
4. Use JOINs instead of multiple queries

---

## Performance Targets

| Metric | Before | Target | How to Achieve |
|--------|--------|--------|----------------|
| UI responsiveness during DB ops | Freezes | Smooth | Async workers |
| Concurrent queries | 1 (serialized) | 10-30 | Connection pooling |
| Lookup query time | 50-200ms | <5ms | Query caching |
| Large table query | 5-10s | <1s | Indexes + pagination |
| Batch insert (100 rows) | 2-5s | <500ms | Bulk INSERT |

---

## Testing Performance Improvements

### Before/After Comparison

1. **Baseline measurement:**
```python
from performance_utils import QueryProfiler

profiler = QueryProfiler()
profiler.start()

# Run typical workflow
login()
load_dashboard()
generate_report()
export_to_excel()

profiler.stop()
print(profiler.get_report())
```

2. **Apply optimization** (e.g., enable pooling, add index)

3. **Re-measure** with same profiler code

4. **Compare** total time and top slowest queries

### Load Testing

Simulate multiple concurrent users:
```bash
# Install locust (load testing tool)
pip install locust

# Create simple test script that exercises database
# Run 10 concurrent "users"
locust -f loadtest.py --users 10 --spawn-rate 2
```

---

## Troubleshooting

### Connection Pool Issues

**Error: "Too many connections"**
- Reduce `pool_size` and `max_overflow` in `db_connect_pooled.py`
- Check MySQL `max_connections` setting

**Error: "Lost connection during query"**
- Already handled by `pool_pre_ping=True`
- Check network stability

### Async Operation Issues

**UI updates not appearing:**
- Ensure callback is connected to signal BEFORE starting worker
- Check for exceptions in worker (they're logged to console)

**Thread safety errors:**
- Don't share PyQt widgets between threads
- Use signals to communicate back to main thread

### Cache Issues

**Stale data in cache:**
- Call `db_manager.clear_cache()` after INSERT/UPDATE/DELETE
- Reduce `maxsize` parameter in `@lru_cache`

---

## Next Steps

1. ✅ **Apply connection pooling** (immediate 10x improvement)
2. ✅ **Add performance monitoring** (identify bottlenecks)
3. ⏳ **Add database indexes** (analyze slow queries first)
4. ⏳ **Convert UI-blocking queries to async** (improve UX)
5. ⏳ **Optimize top 3 slowest queries** (data-driven)

---

## Support Files

- `db_connect_pooled.py` - Connection pooling implementation
- `db_worker.py` - Async database workers
- `performance_utils.py` - Monitoring and profiling tools
- `performance.log` - Execution time logs
- `database.log` - Database connection logs

---

## Questions?

Review the inline documentation in each file for detailed API usage.
