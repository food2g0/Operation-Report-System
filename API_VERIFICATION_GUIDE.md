# API Verification Guide

Complete guide to test and verify your REST API is working correctly.

## 🚀 Quick Verification (5 minutes)

### 1. Check API Server is Running

```powershell
# Test if API server is listening on port 5000
Test-NetConnection -ComputerName localhost -Port 5000

# Expected output:
# ComputerName     : localhost
# RemoteAddress    : 127.0.0.1
# RemotePort       : 5000
# TcpTestSucceeded : True  ← This means API is running!
```

### 2. Check Health Endpoint

```powershell
# Test API health
Invoke-WebRequest http://localhost:5000/api/v1/health

# Expected output:
# StatusCode        : 200
# StatusDescription : OK
```

### 3. Check Response Content

```powershell
# Get JSON response content
$response = Invoke-WebRequest http://localhost:5000/api/v1/health
$response.Content | ConvertFrom-Json

# Expected output:
# status   : healthy
# timestamp: 2024-03-17T10:30:45.123456
# database : connected
```

---

## 📡 Detailed API Testing

### Test 1: Health Check (No Auth Required)

```powershell
# PowerShell
$uri = "http://localhost:5000/api/v1/health"
$response = Invoke-WebRequest -Uri $uri -Method Get

# Check status
if ($response.StatusCode -eq 200) {
    Write-Host "✓ API Health Check: PASSED" -ForegroundColor Green
    $response.Content | ConvertFrom-Json | Format-Table
} else {
    Write-Host "✗ API Health Check: FAILED" -ForegroundColor Red
}
```

### Test 2: Authentication (Login)

```powershell
# Create login credentials
$loginUri = "http://localhost:5000/api/v1/auth/login"
$body = @{
    username = "admin"
    password = "admin"
} | ConvertTo-Json

# Send login request
$response = Invoke-WebRequest -Uri $loginUri `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

# Check response
if ($response.StatusCode -eq 200) {
    Write-Host "✓ Authentication: PASSED" -ForegroundColor Green
    $login_data = $response.Content | ConvertFrom-Json
    $login_data | Format-Table
    
    # Save token for next tests
    $token = $login_data.token
} else {
    Write-Host "✗ Authentication: FAILED" -ForegroundColor Red
    Write-Host "Response: $($response.Content)"
}
```

### Test 3: Verify Token

```powershell
# If login successful, verify the token
if ($token) {
    $headers = @{
        "Authorization" = "Bearer $token"
    }
    
    $verifyUri = "http://localhost:5000/api/v1/auth/verify"
    $response = Invoke-WebRequest -Uri $verifyUri `
        -Headers $headers `
        -Method Get
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Token Verification: PASSED" -ForegroundColor Green
        $response.Content | ConvertFrom-Json | Format-Table
    } else {
        Write-Host "✗ Token Verification: FAILED" -ForegroundColor Red
    }
}
```

### Test 4: Fetch Data (With Authentication)

```powershell
# Get daily reports
if ($token) {
    $reportsUri = "http://localhost:5000/api/v1/reports/daily?limit=5"
    $headers = @{
        "Authorization" = "Bearer $token"
    }
    
    $response = Invoke-WebRequest -Uri $reportsUri `
        -Headers $headers `
        -Method Get
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Fetch Reports: PASSED" -ForegroundColor Green
        $data = $response.Content | ConvertFrom-Json
        Write-Host "Reports found: $($data.count)"
        $data.data | Select-Object -First 3 | Format-Table
    } else {
        Write-Host "✗ Fetch Reports: FAILED" -ForegroundColor Red
    }
}
```

### Test 5: Create Data (POST)

```powershell
# Create a new report
if ($token) {
    $createUri = "http://localhost:5000/api/v1/reports"
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    $body = @{
        client_id = 1
        report_date = "2024-03-17"
        total_amount = 50000
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri $createUri `
        -Headers $headers `
        -Method Post `
        -Body $body
    
    if ($response.StatusCode -eq 201) {
        Write-Host "✓ Create Report: PASSED" -ForegroundColor Green
        $data = $response.Content | ConvertFrom-Json
        Write-Host "New report ID: $($data.report_id)"
        $report_id = $data.report_id
    } else {
        Write-Host "✗ Create Report: FAILED" -ForegroundColor Red
        Write-Host "Response: $($response.Content)"
    }
}
```

### Test 6: Update Data (PUT)

```powershell
# Update the report we just created
if ($token -and $report_id) {
    $updateUri = "http://localhost:5000/api/v1/reports/$report_id"
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    $body = @{
        total_amount = 75000
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri $updateUri `
        -Headers $headers `
        -Method Put `
        -Body $body
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Update Report: PASSED" -ForegroundColor Green
    } else {
        Write-Host "✗ Update Report: FAILED" -ForegroundColor Red
    }
}
```

### Test 7: Delete Data (DELETE)

```powershell
# Delete the report
if ($token -and $report_id) {
    $deleteUri = "http://localhost:5000/api/v1/reports/$report_id"
    $headers = @{
        "Authorization" = "Bearer $token"
    }
    
    $response = Invoke-WebRequest -Uri $deleteUri `
        -Headers $headers `
        -Method Delete
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Delete Report: PASSED" -ForegroundColor Green
    } else {
        Write-Host "✗ Delete Report: FAILED" -ForegroundColor Red
    }
}
```

---

## 🧪 Complete Test Script

Save this as `C:\test_api.ps1` and run it:

```powershell
# API Testing Script
# Run: PowerShell -ExecutionPolicy Bypass -File C:\test_api.ps1

$api_url = "http://localhost:5000"
$test_results = @()

Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "      REST API VERIFICATION TESTS" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "Test 1: Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest "$api_url/api/v1/health" -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ PASSED" -ForegroundColor Green
        $test_results += "Health Check: PASS"
    } else {
        Write-Host "✗ FAILED" -ForegroundColor Red
        $test_results += "Health Check: FAIL"
    }
} catch {
    Write-Host "✗ FAILED - $($_.Exception.Message)" -ForegroundColor Red
    $test_results += "Health Check: FAIL (Exception)"
}
Write-Host ""

# Test 2: Login
Write-Host "Test 2: Authentication (Login)..." -ForegroundColor Yellow
try {
    $loginBody = @{
        username = "admin"
        password = "admin"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest "$api_url/api/v1/auth/login" `
        -Method Post `
        -ContentType "application/json" `
        -Body $loginBody `
        -ErrorAction Stop
    
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        $token = $data.token
        Write-Host "✓ PASSED" -ForegroundColor Green
        Write-Host "  User: $($data.user.username)" -ForegroundColor Gray
        Write-Host "  Role: $($data.user.role)" -ForegroundColor Gray
        $test_results += "Authentication: PASS"
    } else {
        Write-Host "✗ FAILED" -ForegroundColor Red
        $test_results += "Authentication: FAIL"
    }
} catch {
    Write-Host "✗ FAILED - $($_.Exception.Message)" -ForegroundColor Red
    $test_results += "Authentication: FAIL (Exception)"
    $token = $null
}
Write-Host ""

# Test 3: Get Reports
if ($token) {
    Write-Host "Test 3: Fetch Reports..." -ForegroundColor Yellow
    try {
        $headers = @{ "Authorization" = "Bearer $token" }
        $response = Invoke-WebRequest "$api_url/api/v1/reports/daily?limit=5" `
            -Headers $headers `
            -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            $data = $response.Content | ConvertFrom-Json
            Write-Host "✓ PASSED" -ForegroundColor Green
            Write-Host "  Reports found: $($data.count)" -ForegroundColor Gray
            $test_results += "Fetch Reports: PASS"
        } else {
            Write-Host "✗ FAILED" -ForegroundColor Red
            $test_results += "Fetch Reports: FAIL"
        }
    } catch {
        Write-Host "✗ FAILED - $($_.Exception.Message)" -ForegroundColor Red
        $test_results += "Fetch Reports: FAIL (Exception)"
    }
    Write-Host ""
    
    # Test 4: Get Users Profile
    Write-Host "Test 4: Get User Profile..." -ForegroundColor Yellow
    try {
        $headers = @{ "Authorization" = "Bearer $token" }
        $response = Invoke-WebRequest "$api_url/api/v1/users/profile" `
            -Headers $headers `
            -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            $data = $response.Content | ConvertFrom-Json
            Write-Host "✓ PASSED" -ForegroundColor Green
            Write-Host "  Username: $($data.data.username)" -ForegroundColor Gray
            Write-Host "  Email: $($data.data.email)" -ForegroundColor Gray
            $test_results += "User Profile: PASS"
        } else {
            Write-Host "✗ FAILED" -ForegroundColor Red
            $test_results += "User Profile: FAIL"
        }
    } catch {
        Write-Host "✗ FAILED - $($_.Exception.Message)" -ForegroundColor Red
        $test_results += "User Profile: FAIL (Exception)"
    }
    Write-Host ""
    
    # Test 5: Verify Token
    Write-Host "Test 5: Verify Token..." -ForegroundColor Yellow
    try {
        $headers = @{ "Authorization" = "Bearer $token" }
        $response = Invoke-WebRequest "$api_url/api/v1/auth/verify" `
            -Headers $headers `
            -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            $data = $response.Content | ConvertFrom-Json
            Write-Host "✓ PASSED" -ForegroundColor Green
            Write-Host "  Token valid: $($data.valid)" -ForegroundColor Gray
            $test_results += "Token Verify: PASS"
        } else {
            Write-Host "✗ FAILED" -ForegroundColor Red
            $test_results += "Token Verify: FAIL"
        }
    } catch {
        Write-Host "✗ FAILED - $($_.Exception.Message)" -ForegroundColor Red
        $test_results += "Token Verify: FAIL (Exception)"
    }
    Write-Host ""
}

# Summary
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                  SUMMARY" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
$passed = @($test_results | Where-Object { $_ -match "PASS" }).Count
$failed = @($test_results | Where-Object { $_ -match "FAIL" }).Count
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host ""
$test_results | ForEach-Object {
    if ($_ -match "PASS") {
        Write-Host "✓ $_" -ForegroundColor Green
    } else {
        Write-Host "✗ $_" -ForegroundColor Red
    }
}
Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
```

Run the test script:
```powershell
PowerShell -ExecutionPolicy Bypass -File C:\test_api.ps1
```

---

## 🔍 Troubleshooting API Issues

### Issue 1: "Cannot connect to API"

```powershell
# Check if API server is running
Get-Process python | Where-Object { $_.ProcessName -like "*python*" }

# Check if port 5000 is listening
netstat -ano | findstr :5000

# Expected output:
# TCP    0.0.0.0:5000    0.0.0.0:0    LISTENING    12345

# If not listening, start API server:
C:\Users\Admin\Operation-Report-System\.venv\Scripts\python.exe `
    C:\Users\Admin\Operation-Report-System\run_api_server.py
```

### Issue 2: "Authentication Failed"

```powershell
# Check database connection first
Test-NetConnection -ComputerName 192.168.1.100 -Port 3306

# If database connection works, verify credentials
# Default credentials in database:
# username: admin
# password: admin (hashed in database)

# Check if users table has admin user
# Connect to database and run:
# SELECT * FROM users WHERE username = 'admin';
```

### Issue 3: "Database Connection Refused"

```powershell
# Test database connectivity
Test-NetConnection -ComputerName 192.168.1.100 -Port 3306

# If failed:
# 1. Check if database server is running
# 2. Check firewall allows port 3306
# 3. Verify database host in .env

# View current .env settings
Get-Content C:\Users\Admin\Operation-Report-System\.env
```

### Issue 4: "Token Invalid"

```powershell
# Tokens expire after 24 hours
# Solution: Login again to get new token

# Or check JWT settings in .env:
Get-Content C:\Users\Admin\Operation-Report-System\.env | Select-String JWT
```

### Issue 5: "TimeOut - Request took too long"

```powershell
# Check if database is slow
# 1. Check database CPU usage
# 2. Check database memory usage
# 3. Check connection pool status
# 4. Look for long-running queries in database

# Restart API server if high resource usage
nssm restart OperationReportAPI
```

---

## 📊 Performance Verification

### Response Time Test

```powershell
# Measure login response time
$loginUri = "http://localhost:5000/api/v1/auth/login"
$body = @{ username = "admin"; password = "admin" } | ConvertTo-Json

$timer = [System.Diagnostics.Stopwatch]::StartNew()
$response = Invoke-WebRequest $loginUri `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
$timer.Stop()

Write-Host "Login response time: $($timer.ElapsedMilliseconds) ms"
# Expected: < 1000 ms (1 second)
```

### Concurrent Request Test

```powershell
# Test 10 concurrent requests
$uri = "http://localhost:5000/api/v1/health"
$timer = [System.Diagnostics.Stopwatch]::StartNew()

1..10 | ForEach-Object -Parallel {
    Invoke-WebRequest $using:uri
} -ThrottleLimit 10

$timer.Stop()
Write-Host "Time for 10 concurrent requests: $($timer.ElapsedMilliseconds) ms"
# Expected: < 3000 ms (3 seconds)
```

---

## ✅ Verification Checklist

Run through this checklist to verify API is production-ready:

### Basic Functionality
- [ ] Health endpoint returns 200
- [ ] Can login with valid credentials
- [ ] Can login with invalid credentials (returns 401)
- [ ] Token is returned after login
- [ ] Token can be used for authenticated requests
- [ ] Token refresh works
- [ ] Logout clears token

### Data Operations
- [ ] Can fetch reports
- [ ] Can create new report
- [ ] Can update report
- [ ] Can delete report
- [ ] Can fetch user profile
- [ ] Can change password

### Performance
- [ ] Login < 1 second
- [ ] Fetch data < 2 seconds
- [ ] Create data < 2 seconds
- [ ] Response to 10 concurrent requests < 3 seconds

### Security
- [ ] Invalid token rejected
- [ ] Expired token rejected
- [ ] No database credentials in response
- [ ] HTTPS working (if configured)
- [ ] CORS headers present

### Error Handling
- [ ] 400 Bad Request for missing fields
- [ ] 401 Unauthorized for missing token
- [ ] 404 Not Found for invalid resources
- [ ] 500 Internal Server Error has error message

### Logging
- [ ] All requests logged
- [ ] All errors logged with details
- [ ] Log file not growing too fast
- [ ] No sensitive data in logs

---

## 🚀 Advanced Testing with Python

If you prefer Python for testing:

```python
# test_api.py
import requests
import json
from datetime import datetime

class APITester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.token = None
        self.session = requests.Session()
    
    def test_health(self):
        """Test health endpoint"""
        print("Testing health endpoint...")
        response = self.session.get(f"{self.base_url}/api/v1/health")
        assert response.status_code == 200, "Health check failed"
        print(f"✓ Health: {response.json()}")
    
    def test_login(self):
        """Test authentication"""
        print("\nTesting login...")
        data = {"username": "admin", "password": "admin"}
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json=data
        )
        assert response.status_code == 200, "Login failed"
        result = response.json()
        self.token = result['token']
        print(f"✓ Logged in as {result['user']['username']}")
    
    def test_authenticated_request(self):
        """Test authenticated endpoint"""
        print("\nTesting authenticated request...")
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.session.get(
            f"{self.base_url}/api/v1/reports/daily",
            headers=headers
        )
        assert response.status_code == 200, "Authenticated request failed"
        print(f"✓ Got {response.json()['count']} reports")
    
    def run_all_tests(self):
        """Run all tests"""
        print("="*50)
        print("  API Verification Tests")
        print("="*50)
        
        try:
            self.test_health()
            self.test_login()
            self.test_authenticated_request()
            print("\n" + "="*50)
            print("✓ ALL TESTS PASSED")
            print("="*50)
        except Exception as e:
            print(f"\n✗ TEST FAILED: {e}")

if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()
```

Run with:
```bash
python test_api.py
```

---

## 📋 Complete Verification Report Template

Use this template to document your verification:

```
API VERIFICATION REPORT
=======================
Date: ________________
Tested By: ________________
API URL: http://localhost:5000

TEST RESULTS:
==================

1. Health Check
   Status: ✓ PASS / ✗ FAIL
   Response Time: ____ ms
   Notes: ________________

2. Authentication
   Status: ✓ PASS / ✗ FAIL
   Response Time: ____ ms
   Username: admin
   Notes: ________________

3. Data Retrieval
   Status: ✓ PASS / ✗ FAIL
   Records Retrieved: ____
   Response Time: ____ ms
   Notes: ________________

4. Data Creation
   Status: ✓ PASS / ✗ FAIL
   Record ID: ____
   Response Time: ____ ms
   Notes: ________________

5. Data Update
   Status: ✓ PASS / ✗ FAIL
   Response Time: ____ ms
   Notes: ________________

6. Data Deletion
   Status: ✓ PASS / ✗ FAIL
   Response Time: ____ ms
   Notes: ________________

7. Performance Test (10 concurrent)
   Status: ✓ PASS / ✗ FAIL
   Total Time: ____ ms
   Errors: ____
   Notes: ________________

8. Error Handling
   Status: ✓ PASS / ✗ FAIL
   Notes: ________________

OVERALL RESULT:
===============
✓ READY FOR PRODUCTION / ✗ MORE TESTING NEEDED

Issues Found:
1. ________________
2. ________________
3. ________________

Recommendations:
1. ________________
2. ________________

Sign-Off: ________________
```

---

**All tests passing?** ✓ Your API is ready for production!

**Tests failing?** Check log files: `C:\Apps\OperationReportAPI\api.log`
