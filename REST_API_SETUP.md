# REST API Setup Guide

This document provides comprehensive instructions for setting up and using the new REST API layer for the Operation Report System.

## Overview

The REST API provides a centralized, secure interface for all client applications to communicate with the database, eliminating the need for direct database connections. This improves security, maintainability, and scalability.

### Key Benefits

- **Security**: Centralized authentication and authorization
- **Scalability**: Easy to scale API independently from clients
- **Auditability**: All database operations are logged and traceable
- **Maintenance**: Single point of updates for database schema changes
- **Flexibility**: Easy to add new endpoints without modifying clients

## Prerequisites

- Python 3.8 or higher
- All packages from `Requirements.txt` installed
- Valid database credentials in `config.py`
- .env file with API configuration

## Installation

### Step 1: Install Dependencies

```bash
pip install -r Requirements.txt
```

The new dependencies for the API are:
- **Flask**: Web framework for the API
- **Flask-CORS**: Cross-Origin Resource Sharing support
- **PyJWT**: JSON Web Token handling for authentication

### Step 2: Configure Environment

1. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

2. Update `.env` with your settings:

```ini
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=False
API_SECRET_KEY=generate-a-random-secret-key-here
JWT_EXPIRATION_HOURS=24
```

> **⚠️ Important**: Change `API_SECRET_KEY` to a strong random value in production.

### Step 3: Generate Secret Key (Production)

```python
import secrets
print(secrets.token_urlsafe(32))
```

Use the output as your `API_SECRET_KEY`.

## Starting the API Server

### Method 1: Direct Python

```bash
python run_api_server.py
```

### Method 2: Using Flask

```bash
set FLASK_APP=api/app.py
flask run
```

### Method 3: Production (Using Gunicorn)

```bash
pip install gunicorn
gunicorn --workers=4 --bind=0.0.0.0:5000 api.app:app
```

The API will be available at `http://localhost:5000` (or configured port).

## API Architecture

### Project Structure

```
Operation-Report-System/
├── api/
│   ├── __init__.py           # Package initialization
│   ├── app.py                # Main Flask app and routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── database_service.py   # Database operations
│   │   └── auth_service.py       # Authentication handling
│   └── routes/
│       ├── __init__.py
│       ├── reports_routes.py     # Report endpoints
│       ├── users_routes.py       # User management
│       ├── data_routes.py        # Generic data access
│       └── transactions_routes.py # Transaction endpoints
├── api_client.py             # Python client library
├── run_api_server.py        # API entry point
└── .env.example             # Configuration template
```

### Core Components

#### 1. **DatabaseService** (`api/services/database_service.py`)
- Centralized database connection management
- Connection pooling
- Query execution methods (GET, INSERT, UPDATE, DELETE)
- Transaction support

#### 2. **AuthService** (`api/services/auth_service.py`)
- User authentication
- JWT token generation and validation
- Password hashing with bcrypt
- Session management

#### 3. **Route Modules** (`api/routes/`)
- **reports_routes.py**: Report CRUD operations
- **users_routes.py**: User profile and management
- **data_routes.py**: Generic table data access
- **transactions_routes.py**: Transaction and transfer operations

#### 4. **APIClient** (`api_client.py`)
- Python client library for easy API integration
- Token management
- Request/response handling
- Built-in error handling

## API Endpoints

### Authentication Endpoints

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}

Response (200):
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "role": "admin"
  },
  "expires_in": 86400
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer <token>

Response (200):
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_in": 86400
}
```

#### Verify Token
```http
GET /api/v1/auth/verify
Authorization: Bearer <token>

Response (200):
{
  "valid": true,
  "user_id": 1,
  "username": "user@example.com",
  "role": "admin"
}
```

### Health Check
```http
GET /api/v1/health

Response (200):
{
  "status": "healthy",
  "timestamp": "2024-03-17T10:30:45.123456",
  "database": "connected"
}
```

### Reports Endpoints

#### Get Daily Reports
```http
GET /api/v1/reports/daily?date_from=2024-01-01&date_to=2024-03-17&client_id=5
Authorization: Bearer <token>

Response (200):
{
  "success": true,
  "count": 15,
  "data": [...]
}
```

#### Get Report Summary
```http
GET /api/v1/reports/summary?date_from=2024-01-01&date_to=2024-03-17
Authorization: Bearer <token>
```

#### Create Report
```http
POST /api/v1/reports
Authorization: Bearer <token>
Content-Type: application/json

{
  "client_id": 5,
  "report_date": "2024-03-17",
  "total_amount": 50000.00
}

Response (201):
{
  "success": true,
  "message": "Report created successfully",
  "report_id": 123
}
```

#### Update Report
```http
PUT /api/v1/reports/123
Authorization: Bearer <token>
Content-Type: application/json

{
  "total_amount": 55000.00
}
```

#### Delete Report
```http
DELETE /api/v1/reports/123
Authorization: Bearer <token>
```

### Users Endpoints

#### Get User Profile
```http
GET /api/v1/users/profile
Authorization: Bearer <token>

Response (200):
{
  "success": true,
  "data": {
    "id": 1,
    "username": "user@example.com",
    "email": "user@example.com",
    "role": "admin"
  }
}
```

#### Change Password
```http
POST /api/v1/users/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "old_password": "old123",
  "new_password": "new456"
}
```

#### List Users (Admin Only)
```http
GET /api/v1/users?limit=50&offset=0
Authorization: Bearer <admin_token>
```

### Data Endpoints (Generic Table Access)

#### Get Table Data
```http
GET /api/v1/data/clients?limit=100&offset=0&columns=id,name,email
Authorization: Bearer <token>
```

#### Insert Data
```http
POST /api/v1/data/daily_reports
Authorization: Bearer <token>
Content-Type: application/json

{
  "client_id": 5,
  "report_date": "2024-03-17",
  "total_amount": 50000.00
}
```

#### Update Data
```http
PUT /api/v1/data/daily_reports/123
Authorization: Bearer <token>
Content-Type: application/json

{
  "total_amount": 55000.00
}
```

#### Delete Data
```http
DELETE /api/v1/data/daily_reports/123
Authorization: Bearer <token>
```

### Transactions Endpoints

#### Get Transactions
```http
GET /api/v1/transactions?date_from=2024-01-01&date_to=2024-03-17
Authorization: Bearer <token>
```

#### Get Fund Transfers
```http
GET /api/v1/transactions/fund-transfers?status=pending
Authorization: Bearer <token>
```

#### Create Fund Transfer
```http
POST /api/v1/transactions/fund-transfers
Authorization: Bearer <token>
Content-Type: application/json

{
  "from_account": "ACC001",
  "to_account": "ACC002",
  "amount": 10000.00,
  "transfer_date": "2024-03-17"
}
```

#### Approve Fund Transfer
```http
POST /api/v1/transactions/fund-transfers/123/approve
Authorization: Bearer <token>
```

#### Reject Fund Transfer
```http
POST /api/v1/transactions/fund-transfers/123/reject
Authorization: Bearer <token>
Content-Type: application/json

{
  "reason": "Account not verified"
}
```

## Client Migration

See [REST_API_CLIENT_MIGRATION.md](REST_API_CLIENT_MIGRATION.md) for detailed instructions on migrating your PyQt5 clients to use the REST API.

## Error Handling

All API responses follow a standard error format:

```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

### Common HTTP Status Codes

- **200**: Success
- **201**: Created successfully
- **400**: Bad request (validation error)
- **401**: Unauthorized (authentication required or invalid token)
- **403**: Forbidden (permission denied)
- **404**: Not found
- **500**: Internal server error

## Security Best Practices

### 1. API Secret Key
- Generate a strong random key for `API_SECRET_KEY`
- Never commit actual secret to version control
- Rotate keys periodically

### 2. HTTPS
Replace HTTP with HTTPS in production:
```python
# In api/app.py
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
```

### 3. Token Expiration
- Default is 24 hours
- Adjust via `JWT_EXPIRATION_HOURS` in .env
- Token auto-refresh support in client

### 4. CORS Configuration
Restrict CORS origin in production:
```python
# Modify api/app.py
CORS(app, resources={
    r"/api/*": {"origins": ["https://yourdomain.com"]}
})
```

### 5. API Rate Limiting
Consider adding rate limiting in production:
```bash
pip install Flask-Limiter
```

## Logging

The API logs all requests to `api.log`:
```
2024-03-17 10:30:45 - api.app - INFO - POST /api/v1/reports - Status: 201 - User: 1
```

Access logs to monitor:
- Failed authentication attempts
- Unauthorized access attempts
- Database errors
- Performance issues

## Troubleshooting

### API Won't Start
Check:
1. Port 5000 is available: `netstat -an | find ":5000"`
2. Database connection works: Run `test_connection.py`
3. All dependencies installed: `pip list | grep Flask`

### Authentication Failed
- Verify credentials in database
- Check JWT_AEC_KEY is correct
- Ensure user account is active

### Database Connection Issues
- Verify credentials in `config.py` or `.env`
- Check firewall and network connectivity
- Confirm database server is running

### Slow API Responses
- Monitor concurrent requests: `curl http://localhost:5000/api/v1/health`
- Check database query performance
- Consider increasing connection pool size in `DatabaseService`

## Performance Tips

1. **Connection Pooling**: Already configured with pool_size=10
2. **Query Optimization**: Add indexes on frequently queried columns
3. **Pagination**: Always use limit/offset for large result sets
4. **Caching**: Consider Redis for repeated queries
5. **Async Support**: Add async/await for long operations in future

## Next Steps

1. [Migrate your clients to use the API](REST_API_CLIENT_MIGRATION.md)
2. [Set up production deployment](REST_API_DEPLOYMENT.md)
3. Configure monitoring and logging
4. Add rate limiting for production
5. Implement backup authentication methods

## Support

For issues or questions:
1. Check API logs: `api.log`
2. Test health endpoint: `GET /api/v1/health`
3. Verify token: `GET /api/v1/auth/verify`
4. Review error messages in response body

---

**Last Updated**: 2024-03-17
**API Version**: v1.0
