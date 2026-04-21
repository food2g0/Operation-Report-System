# REST API Client Migration Guide

This guide explains how to migrate your PyQt5 clients to use the new REST API instead of direct database connections.

## Before & After Comparison

### Before (Direct Database Connection)

```python
from db_connect_pooled import db_manager

# Direct database query from client
with db_manager.engine.connect() as conn:
    result = conn.execute(
        text("SELECT * FROM daily_reports WHERE client_id = :id"),
        {"id": client_id}
    )
    reports = [dict(row) for row in result]
```

**Problems:**
- Database credentials on every client
- Network traffic goes directly to database
- Difficult to audit who accessed what
- Risk if client is compromised

### After (REST API)

```python
from api_client import APIClient

client = APIClient("http://localhost:5000")
client.login("username", "password")

# API call through secure endpoint
reports = client.get_daily_reports(client_id=client_id)
```

**Benefits:**
- No database credentials on clients
- Centralized authentication
- Easy audit trail
- Single point of security control

## Step-by-Step Migration

### Phase 1: Setup (Before Client Changes)

1. **Start API Server**
   ```bash
   python run_api_server.py
   ```
   Wait for message: `"Starting REST API server on port 5000"`

2. **Verify API is Running**
   ```bash
   curl http://localhost:5000/api/v1/health
   ```
   Should return `{"status": "healthy", ...}`

### Phase 2: Update Client Imports

Replace database imports with API client:

**Old:**
```python
from db_connect_pooled import db_manager
from sqlalchemy import text
```

**New:**
```python
from api_client import APIClient

# Initialize at module/class level
api = APIClient("http://localhost:5000")
```

### Phase 3: Replace Database Calls

#### Example 1: Fetching Reports

**Old Code:**
```python
def load_reports(self):
    try:
        query = """
            SELECT id, report_date, amount 
            FROM daily_reports 
            WHERE client_id = :client_id
            ORDER BY report_date DESC
        """
        with db_manager.engine.connect() as conn:
            result = conn.execute(
                text(query),
                {"client_id": self.client_id}
            )
            self.reports = [dict(row) for row in result]
    except Exception as e:
        print(f"Error: {e}")
```

**New Code:**
```python
def load_reports(self):
    try:
        self.reports = api.get_daily_reports(client_id=self.client_id)
        if self.reports is None:
            raise Exception("Failed to fetch reports")
    except Exception as e:
        print(f"Error: {e}")
```

#### Example 2: Creating Records

**Old Code:**
```python
def save_report(self, data):
    try:
        query = """
            INSERT INTO daily_reports 
            (client_id, report_date, amount, created_by, created_date)
            VALUES (:client_id, :report_date, :amount, :user_id, NOW())
        """
        with db_manager.engine.begin() as conn:
            conn.execute(
                text(query),
                {
                    "client_id": data["client_id"],
                    "report_date": data["report_date"],
                    "amount": data["amount"],
                    "user_id": self.current_user_id
                }
            )
            conn.commit()
        return True
    except Exception as e:
        return False
```

**New Code:**
```python
def save_report(self, data):
    try:
        report_id = api.create_report({
            "client_id": data["client_id"],
            "report_date": data["report_date"],
            "total_amount": data["amount"]
        })
        return report_id is not None
    except Exception as e:
        return False
```

#### Example 3: Updating Records

**Old Code:**
```python
def update_report(self, report_id, new_amount):
    try:
        query = """
            UPDATE daily_reports 
            SET amount = :amount, modified_date = NOW()
            WHERE id = :report_id
        """
        with db_manager.engine.begin() as conn:
            conn.execute(
                text(query),
                {"amount": new_amount, "report_id": report_id}
            )
            conn.commit()
        return True
    except Exception as e:
        return False
```

**New Code:**
```python
def update_report(self, report_id, new_amount):
    try:
        return api.update_report(report_id, {"total_amount": new_amount})
    except Exception as e:
        return False
```

#### Example 4: Deleting Records

**Old Code:**
```python
def delete_report(self, report_id):
    try:
        query = "DELETE FROM daily_reports WHERE id = :report_id"
        with db_manager.engine.begin() as conn:
            conn.execute(text(query), {"report_id": report_id})
            conn.commit()
        return True
    except Exception as e:
        return False
```

**New Code:**
```python
def delete_report(self, report_id):
    try:
        return api.delete_report(report_id)
    except Exception as e:
        return False
```

#### Example 5: Generic Table Queries

**Old Code:**
```python
def get_clients(self):
    query = "SELECT id, name, email FROM clients LIMIT 100"
    with db_manager.engine.connect() as conn:
        result = conn.execute(text(query))
        return [dict(row) for row in result]
```

**New Code:**
```python
def get_clients(self):
    return api.get_table_data(
        'clients',
        columns=['id', 'name', 'email'],
        limit=100
    )
```

### Phase 4: Implement Authentication

Add login dialog when application starts:

```python
from PyQt5.QtWidgets import QMessageBox, QInputDialog

def authenticate_user(self):
    # Get credentials from login dialog
    username, ok = QInputDialog.getText(None, "Login", "Username:")
    if not ok:
        return False
    
    password, ok = QInputDialog.getText(None, "Login", "Password:", 
                                        QLineEdit.Password)
    if not ok:
        return False
    
    # Authenticate with API
    if api.login(username, password):
        self.current_user_id = api.user_id
        return True
    else:
        QMessageBox.critical(None, "Login Failed", "Invalid credentials")
        return False

def on_startup(self):
    if not authenticate_user(self):
        self.close()
        return
    # Continue with normal app startup
```

### Phase 5: Initialize API Client in Main Files

Update your main entry point:

**Old client_dashboard.py:**
```python
from db_connect_pooled import db_manager

class ClientDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        # Connect to database
        if not db_manager.connect():
            raise Exception("Database connection failed")
```

**New client_dashboard.py:**
```python
from api_client import APIClient

class ClientDashboard(QMainWindow):
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api = api_client
        # Check API connection
        if not self.api.health_check():
            raise Exception("API connection failed")
```

Update login.py or main.py:

```python
from api_client import APIClient
from Client.client_dashboard import ClientDashboard

def main():
    app = QApplication(sys.argv)
    
    # Initialize API client
    api = APIClient(os.getenv('API_URL', 'http://localhost:5000'))
    
    # Show login window
    login_window = LoginWindow(api)
    if login_window.exec() == QDialog.Accepted:
        dashboard = ClientDashboard(api)
        dashboard.show()
        sys.exit(app.exec())
    
    sys.exit(0)
```

## Common Patterns

### Pattern 1: Search/Filter

**Old:**
```python
def search_reports(self, search_term):
    query = f"""
        SELECT * FROM daily_reports 
        WHERE report_name LIKE :term
    """
    with db_manager.engine.connect() as conn:
        result = conn.execute(text(query), {"term": f"%{search_term}%"})
        return [dict(row) for row in result]
```

**New:**
```python
def search_reports(self, search_term):
    # Use generic API with SQL-like query
    # Or implement dedicated endpoint in API
    reports = api.get_table_data('daily_reports', limit=1000)
    return [r for r in reports if search_term.lower() in str(r).lower()]
```

### Pattern 2: Date Range Queries

**Old:**
```python
def get_reports_in_range(self, start_date, end_date):
    query = """
        SELECT * FROM daily_reports 
        WHERE report_date BETWEEN :start AND :end
    """
    with db_manager.engine.connect() as conn:
        result = conn.execute(text(query), 
                            {"start": start_date, "end": end_date})
        return [dict(row) for row in result]
```

**New:**
```python
def get_reports_in_range(self, start_date, end_date):
    return api.get_daily_reports(
        date_from=start_date,
        date_to=end_date
    )
```

### Pattern 3: Batch Operations

**Old:**
```python
def import_reports(self, report_list):
    with db_manager.engine.begin() as conn:
        for report in report_list:
            conn.execute(text(
                "INSERT INTO daily_reports VALUES (...)"
            ), report)
        conn.commit()
```

**New:**
```python
def import_reports(self, report_list):
    for report in report_list:
        api.create_report(report)
```

## Error Handling

### Network Errors

```python
try:
    reports = api.get_daily_reports()
except requests.ConnectionError:
    QMessageBox.warning(None, "Connection Error", 
                       "Cannot connect to API server")
except Exception as e:
    QMessageBox.critical(None, "Error", f"Failed to fetch reports: {e}")
```

### Authentication Errors

```python
if not api.is_authenticated():
    # Re-authenticate
    if not authenticate_user():
        return  # Exit operation
```

### Token Expiration

```python
if api.token_expired():
    if not api.refresh_token():
        # Re-authenticate
        authenticate_user()
```

## Configuration for Clients

Create `client_config.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

API_CONFIG = {
    'base_url': os.getenv('API_BASE_URL', 'http://localhost:5000'),
    'timeout': int(os.getenv('API_TIMEOUT', 30)),
    'retry_attempts': 3,
    'cache_enabled': True,
    'cache_ttl': 300,  # seconds
}
```

## Testing Migration

Create `test_api_client.py` to verify:

```python
from api_client import APIClient

def test_api_client():
    api = APIClient('http://localhost:5000')
    
    # Test 1: Health check
    print("Testing health check...")
    assert api.health_check(), "Health check failed"
    print("✓ Health check passed")
    
    # Test 2: Login
    print("Testing login...")
    assert api.login('testuser', 'password'), "Login failed"
    print("✓ Login passed")
    
    # Test 3: Get reports
    print("Testing get_daily_reports...")
    reports = api.get_daily_reports()
    print(f"✓ Got {len(reports)} reports")
    
    # Test 4: Get profile
    print("Testing get_user_profile...")
    profile = api.get_user_profile()
    assert profile is not None, "Profile fetch failed"
    print(f"✓ Got profile for {profile['username']}")
    
    print("\n✓ All tests passed!")

if __name__ == '__main__':
    test_api_client()
```

Run tests:
```bash
python test_api_client.py
```

## Rollback Plan

If issues occur during migration:

1. **Keep database connection code** in a separate branch
2. **Feature flag** for API vs database:
   ```python
   USE_API = os.getenv('USE_API', 'true').lower() == 'true'
   
   if USE_API:
       reports = api.get_daily_reports()
   else:
       reports = db_manager.get_reports()
   ```
3. **Easy switch** to previous version via environment variable

## Performance Considerations

### Before
- Multiple clients with independent connections
- Variable latency based on network
- Database connection overhead per client

### After
- Single API server with connection pooling
- Consistent, optimized connection handling
- Network latency + API processing time

**Optimization:**
- Keep API server on same network as database
- Use HTTP/2 when possible
- Implement request caching for read-heavy operations

## Monitoring

Monitor API performance:

```python
import time

start = time.time()
reports = api.get_daily_reports()
elapsed = time.time() - start

print(f"API call took {elapsed:.2f} seconds")
if elapsed > 2.0:
    print("⚠️ Slow API response - check server")
```

## Migration Checklist

- [ ] API server started and tested
- [ ] Updated Requirements.txt
- [ ] Created .env file with API configuration
- [ ] Updated client imports
- [ ] Replaced database calls with API calls
- [ ] Implemented authentication
- [ ] Added error handling
- [ ] Tested with actual data
- [ ] Verified audit logs
- [ ] Documented custom queries
- [ ] Trained users on changes
- [ ] Removed database credentials from clients
- [ ] Disabled direct database access (optional)

## Troubleshooting Migration

### Issue: "Cannot connect to API"
- Verify API server is running
- Check firewall rules
- Verify URL in client config

### Issue: "Authentication failed"
- Verify credentials in database
- Check JWT token expiration
- Look for error in api.log

### Issue: "Slow API responses"
- Check if database is overloaded
- Monitor API server CPU/memory
- Look for slow queries in logs

### Issue: "Data not updated"
- Verify network connectivity
- Check API response status codes
- Review API logs for errors

## Support

For detailed API documentation, see [REST_API_SETUP.md](REST_API_SETUP.md).

---

**Last Updated**: 2024-03-17
**Migration Version**: v1.0
