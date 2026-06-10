# Performance Optimization for Large Datasets (Millions of Records)

This guide ensures your system remains fast and smooth even with massive amounts of data.

## 1. Database Indexing (Most Critical)

Proper indexes can make queries 100-1000x faster!

### Current Tables That Need Indexing

```sql
-- daily_reports table (heavily queried)
ALTER TABLE daily_reports ADD INDEX idx_date_branch (date, branch);
ALTER TABLE daily_reports ADD INDEX idx_corporation_date (corporation, date);
ALTER TABLE daily_reports ADD INDEX idx_branch (branch);

-- daily_reports_brand_a table
ALTER TABLE daily_reports_brand_a ADD INDEX idx_date_branch (date, branch);
ALTER TABLE daily_reports_brand_a ADD INDEX idx_corporation_date (corporation, date);

-- payable_tbl_brand_a table (consolidated source)
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_date_branch (date, branch);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_corporation_date (corporation, date);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_branch (branch);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_corporation (corporation);

-- General indexes for common WHERE clauses
ALTER TABLE daily_reports ADD INDEX idx_status (status);
ALTER TABLE daily_reports ADD INDEX idx_category (category_filter);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_sendout_capital (sendout_capital);
```

### Index Creation Script

Create `create_indexes.sql`:

```sql
-- Phase 1: Critical indexes (create first, fastest queries)
ALTER TABLE daily_reports ADD INDEX idx_date_branch (date, branch);
ALTER TABLE daily_reports_brand_a ADD INDEX idx_date_branch (date, branch);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_date_branch (date, branch);

-- Phase 2: Common filters
ALTER TABLE daily_reports ADD INDEX idx_corporation_date (corporation, date);
ALTER TABLE daily_reports_brand_a ADD INDEX idx_corporation_date (corporation, date);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_corporation_date (corporation, date);

-- Phase 3: Additional columns
ALTER TABLE daily_reports ADD INDEX idx_branch (branch);
ALTER TABLE daily_reports ADD INDEX idx_status (status);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_branch (branch);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_corporation (corporation);
```

### Run Indexes

```bash
mysql -h localhost -u root -p operation_report_system < create_indexes.sql
```

### Monitor Index Usage

Check if indexes are being used:

```sql
-- Find unused indexes
SELECT * FROM sys.schema_unused_indexes;

-- Check query execution plan
EXPLAIN SELECT * FROM daily_reports WHERE date='2026-06-10' AND branch='Makati';
```

---

## 2. Query Optimization

### ❌ BAD: Loading ALL data at once

```python
# Loads millions of rows into memory - SLOW and CRASHES
result = db.execute_query("SELECT * FROM daily_reports")  # ❌ BAD
all_data = result[0]  # Memory overload!
```

### ✅ GOOD: Pagination with date ranges

```python
# Load data in chunks by date - FAST
def load_reports_paginated(start_date, end_date, batch_size=1000):
    for offset in range(0, total_records, batch_size):
        query = """
            SELECT * FROM daily_reports 
            WHERE date BETWEEN %s AND %s
            LIMIT %s OFFSET %s
        """
        result = db.execute_query(query, (start_date, end_date, batch_size, offset))
        yield result  # Process one batch at a time
```

### ❌ BAD: N+1 Query Problem

```python
# Makes millions of queries - VERY SLOW
branches = db.execute_query("SELECT DISTINCT branch FROM daily_reports")
for branch in branches:
    # This query runs for EVERY branch!
    details = db.execute_query("SELECT * FROM daily_reports WHERE branch=%s", (branch,))
```

### ✅ GOOD: Single JOIN query

```python
# Single query with JOIN - FAST
query = """
    SELECT d.*, b.branch_details 
    FROM daily_reports d
    LEFT JOIN branch_info b ON d.branch = b.name
    WHERE d.date BETWEEN %s AND %s
"""
result = db.execute_query(query, (start_date, end_date))
```

### Query Performance Tips

1. **Use WHERE clauses with indexed columns**
   ```sql
   SELECT * FROM daily_reports 
   WHERE date >= '2026-01-01'  -- Indexed: FAST
   AND branch = 'Makati';      -- Indexed: FAST
   ```

2. **Avoid SELECT \* when you need specific columns**
   ```python
   # ❌ Bad: Gets all columns
   SELECT * FROM daily_reports WHERE date='2026-06-10'
   
   # ✅ Good: Only needed columns
   SELECT date, branch, corporation, sendout_capital, payout_capital 
   FROM daily_reports WHERE date='2026-06-10'
   ```

3. **Use LIMIT to reduce result size**
   ```sql
   SELECT * FROM daily_reports 
   WHERE date='2026-06-10' 
   LIMIT 100;  -- Only 100 rows
   ```

---

## 3. Data Pagination & Lazy Loading

### Implement Pagination in UI

```python
def load_report_data_paginated(start_date, end_date, page=1, page_size=100):
    """Load data in pages instead of all at once"""
    offset = (page - 1) * page_size
    
    query = """
        SELECT * FROM daily_reports 
        WHERE date BETWEEN %s AND %s
        ORDER BY date DESC
        LIMIT %s OFFSET %s
    """
    
    result = db.execute_query(query, (start_date, end_date, page_size, offset))
    
    # Get total count for pagination UI
    count_query = """
        SELECT COUNT(*) as total FROM daily_reports 
        WHERE date BETWEEN %s AND %s
    """
    count_result = db.execute_query(count_query, (start_date, end_date))
    total = count_result[0]['total']
    
    return {
        'data': result,
        'page': page,
        'page_size': page_size,
        'total': total,
        'total_pages': (total + page_size - 1) // page_size
    }
```

### Load Data Only When Needed

```python
class ReportData:
    def __init__(self, date, branch):
        self.date = date
        self.branch = branch
        self._data = None  # Lazy loaded
    
    @property
    def data(self):
        if self._data is None:
            # Only load when accessed
            self._data = db.execute_query(
                "SELECT * FROM daily_reports WHERE date=%s AND branch=%s",
                (self.date, self.branch)
            )
        return self._data
```

---

## 4. Caching Strategy

### Application-Level Cache

```python
from functools import lru_cache
from datetime import datetime, timedelta

class ReportCache:
    def __init__(self, ttl_minutes=60):
        self.cache = {}
        self.ttl_minutes = ttl_minutes
    
    def get(self, key):
        if key not in self.cache:
            return None
        
        data, timestamp = self.cache[key]
        if datetime.now() - timestamp > timedelta(minutes=self.ttl_minutes):
            del self.cache[key]
            return None
        
        return data
    
    def set(self, key, value):
        self.cache[key] = (value, datetime.now())
    
    def invalidate(self, key):
        if key in self.cache:
            del self.cache[key]

# Usage
cache = ReportCache(ttl_minutes=30)

def get_branch_data(date, branch):
    cache_key = f"{date}_{branch}"
    
    # Return cached if available
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    
    # Load from database if not cached
    result = db.execute_query(
        "SELECT * FROM daily_reports WHERE date=%s AND branch=%s",
        (date, branch)
    )
    
    # Store in cache
    cache.set(cache_key, result)
    return result
```

### Database Query Cache

```sql
-- MySQL Query Cache (simple but effective)
SET SESSION query_cache_type = ON;

-- Check query cache stats
SHOW STATUS LIKE 'Qcache%';

-- View cached queries
SELECT * FROM performance_schema.table_io_waits_summary_by_table;
```

---

## 5. Connection Pooling

### Current API Manager Already Has Connection Pool

```python
# api_db_manager.py already uses session pooling with HTTPAdapter
adapter = HTTPAdapter(max_retries=retry)
self._session.mount("http://", adapter)
```

### Optimize Connection Pool Settings

```python
# In api_db_manager.py
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Create session with connection pooling
session = requests.Session()

# Pool connections for reuse
adapter = HTTPAdapter(
    pool_connections=10,      # Number of pools
    pool_maxsize=20,          # Max connections per pool
    max_retries=Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
)

session.mount('http://', adapter)
session.mount('https://', adapter)
```

---

## 6. Data Partitioning/Archiving

### Archive Old Data (Older Than 1 Year)

```python
def archive_old_reports(cutoff_date):
    """Move reports older than cutoff_date to archive table"""
    
    # Create archive table if not exists
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS daily_reports_archive LIKE daily_reports
    """)
    
    # Move old data to archive
    db.execute_query("""
        INSERT INTO daily_reports_archive 
        SELECT * FROM daily_reports 
        WHERE date < %s
    """, (cutoff_date,))
    
    # Delete from active table
    db.execute_query("""
        DELETE FROM daily_reports 
        WHERE date < %s
    """, (cutoff_date,))
    
    print(f"✓ Archived reports before {cutoff_date}")
```

### Query Archived Data When Needed

```python
def get_historical_report(date, branch):
    """Get data from archive if date is old"""
    
    cutoff_date = datetime.now() - timedelta(days=365)
    
    if date < cutoff_date.date():
        # Query archive table
        return db.execute_query(
            "SELECT * FROM daily_reports_archive WHERE date=%s AND branch=%s",
            (date, branch)
        )
    else:
        # Query active table
        return db.execute_query(
            "SELECT * FROM daily_reports WHERE date=%s AND branch=%s",
            (date, branch)
        )
```

---

## 7. Monitoring & Profiling

### Check Query Performance

```python
import time

def profile_query(query_name, query, params):
    """Measure query execution time"""
    start = time.time()
    result = db.execute_query(query, params)
    elapsed = time.time() - start
    
    print(f"[{query_name}] Executed in {elapsed:.3f}s, {len(result)} rows")
    
    # Log slow queries (> 1 second)
    if elapsed > 1.0:
        logger.warning(f"SLOW QUERY: {query_name} took {elapsed:.3f}s")
    
    return result
```

### Monitor Database Health

```sql
-- Check table size
SELECT 
    TABLE_NAME,
    ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) AS `Size_MB`
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'operation_report_system'
ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC;

-- Check for missing indexes
SELECT * FROM sys.schema_unused_indexes;

-- Check slow queries log
SELECT * FROM mysql.slow_log;

-- Check index statistics
SELECT * FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = 'operation_report_system'
ORDER BY TABLE_NAME, SEQ_IN_INDEX;
```

### Create Slow Query Log

```sql
-- Enable slow query logging (queries taking > 1 second)
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;

-- View slow queries
SELECT * FROM mysql.slow_log WHERE query_time > 1;
```

---

## 8. Database Optimization Commands

### Analyze Table Statistics

```sql
-- Update statistics for better query planning
ANALYZE TABLE daily_reports;
ANALYZE TABLE daily_reports_brand_a;
ANALYZE TABLE payable_tbl_brand_a;
```

### Optimize Table

```sql
-- Reclaim unused space and optimize table structure
OPTIMIZE TABLE daily_reports;
OPTIMIZE TABLE daily_reports_brand_a;
OPTIMIZE TABLE payable_tbl_brand_a;
```

### Check Table Integrity

```sql
-- Check for corruption
CHECK TABLE daily_reports;
CHECK TABLE daily_reports_brand_a;
CHECK TABLE payable_tbl_brand_a;
```

---

## 9. Implementation Checklist

### Phase 1: Immediate (Biggest Impact)
- [ ] Create indexes on frequently queried columns (date, branch, corporation)
- [ ] Implement pagination in report loading
- [ ] Run ANALYZE TABLE on all main tables
- [ ] Check for slow queries with EXPLAIN

### Phase 2: Short-term
- [ ] Implement application-level caching
- [ ] Optimize queries to fetch only needed columns
- [ ] Add connection pooling settings
- [ ] Monitor query execution times

### Phase 3: Medium-term
- [ ] Implement data archiving for old records
- [ ] Set up slow query logging
- [ ] Create query performance dashboard
- [ ] Optimize index strategy based on usage

### Phase 4: Long-term
- [ ] Consider table partitioning by date
- [ ] Implement read replicas for reporting
- [ ] Set up automated index maintenance
- [ ] Regular database maintenance schedule

---

## 10. Expected Performance Improvements

With proper optimization:

| Scenario | Without Optimization | With Optimization | Improvement |
|----------|-------------------|------------------|------------|
| Load 1 year of reports | 30-60 seconds | 0.5-2 seconds | 15-60x faster |
| Search by date+branch | 5-10 seconds | 0.05-0.1 seconds | 50-100x faster |
| Generate report | 45-90 seconds | 2-5 seconds | 10-20x faster |
| UI responsiveness | Slow, freezes | Instant, smooth | Noticeable difference |
| Database CPU usage | 90-100% | 10-30% | Much lower load |

---

## 11. Commands to Run Now

### Create All Indexes

```bash
mysql -u root -p operation_report_system << 'EOF'
ALTER TABLE daily_reports ADD INDEX idx_date_branch (date, branch);
ALTER TABLE daily_reports ADD INDEX idx_corporation_date (corporation, date);
ALTER TABLE daily_reports ADD INDEX idx_branch (branch);
ALTER TABLE daily_reports ADD INDEX idx_status (status);

ALTER TABLE daily_reports_brand_a ADD INDEX idx_date_branch (date, branch);
ALTER TABLE daily_reports_brand_a ADD INDEX idx_corporation_date (corporation, date);

ALTER TABLE payable_tbl_brand_a ADD INDEX idx_date_branch (date, branch);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_corporation_date (corporation, date);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_branch (branch);
ALTER TABLE payable_tbl_brand_a ADD INDEX idx_corporation (corporation);

ANALYZE TABLE daily_reports;
ANALYZE TABLE daily_reports_brand_a;
ANALYZE TABLE payable_tbl_brand_a;
EOF
```

### Check Performance Improvement

After creating indexes, run the same queries and compare execution time:

```sql
EXPLAIN SELECT * FROM daily_reports 
WHERE date='2026-06-10' AND branch='Makati' LIMIT 100;
```

---

## Summary

With millions of records, the key is:
1. **Indexes** (fastest impact) - 50-100x improvement
2. **Pagination** - Avoid loading all data
3. **Caching** - Reduce database queries
4. **Monitoring** - Identify bottlenecks
5. **Archiving** - Keep active table small

Start with indexes and pagination - they have the biggest impact!
