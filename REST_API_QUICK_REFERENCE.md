# REST API Quick Reference

Fast reference guide for developers using the REST API.

## Quick Start

### 1. Start API Server
```bash
python run_api_server.py
```

### 2. Login
```python
from api_client import APIClient

api = APIClient('http://localhost:5000')
api.login('username', 'password')
```

### 3. Use API
```python
# Fetch reports
reports = api.get_daily_reports(date_from='2024-01-01')

# Create report
report_id = api.create_report({
    'client_id': 1,
    'report_date': '2024-03-17',
    'total_amount': 50000
})

# Update report
api.update_report(report_id, {'total_amount': 55000})

# Delete report
api.delete_report(report_id)
```

## API Endpoints Summary

### Authentication
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /api/v1/auth/login | Login and get token |
| POST | /api/v1/auth/refresh | Refresh JWT token |
| GET | /api/v1/auth/verify | Verify token validity |

### Reports
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /api/v1/reports/daily | Get daily reports |
| GET | /api/v1/reports/summary | Get summary statistics |
| GET | /api/v1/reports/{id} | Get single report |
| POST | /api/v1/reports | Create report |
| PUT | /api/v1/reports/{id} | Update report |
| DELETE | /api/v1/reports/{id} | Delete report |

### Users
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /api/v1/users/profile | Get user profile |
| PUT | /api/v1/users/profile | Update profile |
| POST | /api/v1/users/change-password | Change password |
| GET | /api/v1/users | List all users (admin) |
| GET | /api/v1/users/{id} | Get user (admin) |

### Generic Data
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /api/v1/data/{table} | Get table data |
| POST | /api/v1/data/{table} | Insert row |
| PUT | /api/v1/data/{table}/{id} | Update row |
| DELETE | /api/v1/data/{table}/{id} | Delete row |

### Transactions
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /api/v1/transactions | Get transactions |
| GET | /api/v1/transactions/{id} | Get transaction |
| GET | /api/v1/transactions/fund-transfers | Get fund transfers |
| POST | /api/v1/transactions/fund-transfers | Create transfer |
| POST | /api/v1/transactions/fund-transfers/{id}/approve | Approve transfer |
| POST | /api/v1/transactions/fund-transfers/{id}/reject | Reject transfer |

### Utility
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /api/v1/health | Health check |

## Common Response Format

### Success Response
```json
{
  "success": true,
  "data": {...},
  "message": "Operation successful"
}
```

### Error Response
```json
{
  "error": "Error type",
  "message": "Description of error"
}
```

## HTTP Status Codes
- **200**: OK - Request successful
- **201**: Created - Resource created successfully
- **400**: Bad Request - Invalid input
- **401**: Unauthorized - Authentication required
- **403**: Forbidden - Permission denied
- **404**: Not Found - Resource not found
- **500**: Server Error - Internal error

## Environment Variables

```ini
API_HOST=0.0.0.0          # API server host
API_PORT=5000             # API server port
API_DEBUG=False           # Debug mode (false in production)
API_SECRET_KEY=...        # JWT secret key
JWT_EXPIRATION_HOURS=24   # Token expiration
```

## APIClient Methods

### Authentication
```python
api.login(username, password)          # Login
api.logout()                           # Logout
api.refresh_token()                    # Refresh token
api.is_authenticated()                 # Check auth status
api.health_check()                     # Check API health
```

### Reports
```python
api.get_daily_reports(date_from, date_to, client_id)
api.get_report_summary(date_from, date_to)
api.get_report(report_id)
api.create_report(data)
api.update_report(report_id, data)
api.delete_report(report_id)
```

### Users
```python
api.get_user_profile()
api.update_user_profile(data)
api.change_password(old_password, new_password)
```

### Generic Data
```python
api.get_table_data(table_name, columns, limit, offset)
api.insert_table_data(table_name, data)
api.update_table_data(table_name, record_id, data)
api.delete_table_data(table_name, record_id)
```

### Transactions
```python
api.get_transactions(date_from, date_to, client_id, transaction_type)
api.get_fund_transfers(status, date_from, date_to)
api.create_fund_transfer(from_account, to_account, amount, transfer_date)
api.approve_fund_transfer(transfer_id)
api.reject_fund_transfer(transfer_id, reason)
```

## Error Handling

```python
try:
    report_id = api.create_report(data)
    if report_id is None:
        print("Failed to create report")
except Exception as e:
    print(f"Error: {e}")
```

## Pagination

```python
# Get page 2 (50 items per page)
reports = api.get_daily_reports(limit=50, offset=50)

# Parameters:
# limit: items per page (default 100, max 1000)
# offset: number of items to skip
```

## Filtering

```python
# Date range
reports = api.get_daily_reports(
    date_from='2024-01-01',
    date_to='2024-03-17'
)

# By client
reports = api.get_daily_reports(client_id=5)

# By status
transfers = api.get_fund_transfers(status='pending')
```

## Creating/Updating Data

```python
# Create new record
new_data = {
    'client_id': 1,
    'report_date': '2024-03-17',
    'total_amount': 50000
}
report_id = api.create_report(new_data)

# Update existing record
update_data = {
    'total_amount': 55000,
    'status': 'completed'
}
success = api.update_report(report_id, update_data)
```

## Authentication Header Format

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

The API client handles this automatically. If making raw HTTP requests:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:5000/api/v1/reports/daily
```

## Logging

API logs go to `api.log`:

```
2024-03-17 10:30:45 - api.app - INFO - POST /api/v1/reports - Status: 201 - User: 1
2024-03-17 10:31:15 - api.app - ERROR - Query execution failed: [error details]
```

Monitor for:
- Unauthorized attempts
- Failed queries
- Slow endpoints
- Database connection issues

## Performance Tips

1. **Pagination**: Always use limit/offset for large datasets
   ```python
   api.get_table_data('reports', limit=100, offset=0)
   ```

2. **Selective Columns**: Only fetch needed columns
   ```python
   api.get_table_data('clients', columns=['id', 'name', 'email'])
   ```

3. **Connection Reuse**: Keep API client instance
   ```python
   # Good
   api = APIClient(...)
   api.login(...)
   # Reuse api for multiple calls
   
   # Bad - creates new connection each time
   for item in items:
       api = APIClient(...)  # Don't do this
   ```

4. **Token Refresh**: Handle token expiration
   ```python
   if not response:
       api.refresh_token()
       retry_operation()
   ```

## Debugging

### Enable logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check API health
```python
if api.health_check():
    print("API is healthy")
else:
    print("API is down")
```

### Verify token
```python
if api.is_authenticated():
    print(f"Logged in as {api.username}")
```

### Test raw endpoint
```bash
curl http://localhost:5000/api/v1/health
```

## Useful Commands

### Check API status
```bash
curl http://localhost:5000/api/v1/health
```

### View API logs
```bash
tail -f api.log
# or
Get-Content api.log -Tail 20  # PowerShell
```

### Restart API server
```bash
# Stop current process and run:
python run_api_server.py
```

### Test login
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'
```

## Database Schema Requirements

The API expects these tables and columns for core functionality:

### users table
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50),  -- 'admin', 'user', 'viewer'
    is_active BOOLEAN DEFAULT TRUE,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified_date DATETIME,
    modified_by INT
);
```

### daily_reports table
```sql
CREATE TABLE daily_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    client_id INT NOT NULL,
    report_date DATE NOT NULL,
    total_amount DECIMAL(15,2),
    created_by INT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified_date DATETIME,
    modified_by INT,
    deleted_date DATETIME,
    deleted_by INT,
    is_deleted BOOLEAN DEFAULT FALSE
);
```

### field_config table (optional)
```sql
CREATE TABLE field_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSON
);
```

Add audit fields to other tables as needed:
- `created_by` (INT)
- `created_date` (DATETIME)
- `modified_by` (INT)
- `modified_date` (DATETIME)
- `deleted_by` (INT)
- `deleted_date` (DATETIME)
- `is_deleted` (BOOLEAN)

## Limitations & Future Work

**Current:**
- Single API server (no clustering)
- No built-in caching
- No request rate limiting
- Token expires after 24 hours

**Planned:**
- Redis caching layer
- Rate limiting
- API key authentication
- Webhook support
- Request versioning
- GraphQL endpoint

---

**Quick Help**: Check [REST_API_SETUP.md](REST_API_SETUP.md) for detailed docs

**Last Updated**: 2024-03-17
