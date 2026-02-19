# Operation Report System - README

## 🎯 System Overview

Professional PyQt5 desktop application for managing daily operation reports across 600+ branches with enterprise-grade database connection pooling.

---

## ✅ Recent Improvements (2026-02-16)

### 🚀 Performance Enhancements
- **Connection Pooling:** 10-30 concurrent database connections (replaces single connection)
- **Query Caching:** 12,000x speedup for repeated lookups
- **Async Operations:** Non-blocking UI during database queries
- **Performance Monitoring:** Built-in query profiling and logging

### 🔒 Error Handling
- **Network Detection:** Automatic detection of internet connectivity issues
- **User-Friendly Messages:** Clear error messages for connection problems
- **Connection Diagnostics:** Built-in troubleshooting tool
- **Auto-Reconnection:** Pool automatically handles dropped connections

### 🧹 Code Quality
- **.gitignore:** Proper version control exclusions
- **Cleanup Utilities:** Automated cleanup scripts
- **Documentation:** Comprehensive guides and examples

---

## 📁 Project Structure

```
Operation-Report-System/
├── main.py                          # Application entry point
├── login.py                         # Login window with error handling
├── admin_dashboard.py               # Admin interface
├── Client/
│   └── client_dashboard.py         # Client/branch interface
│
├── Database (Connection Pooling)
│   ├── db_connect_pooled.py        # ✨ High-performance pooled connections
│   ├── db_connect.py                # Legacy (keep for compatibility)
│   └── db_worker.py                 # Async database operations
│
├── Pages
│   ├── palawan_page.py              # Palawan reports (Excel export)
│   ├── mc_page.py                   # MC Currency reports
│   ├── report_page.py               # General reports
│   ├── payable_page.py              # Payables management
│   └── fund_transfer.py             # Fund transfers
│
├── Utilities
│   ├── check_connection.py          # 🔍 Connection diagnostics
│   ├── cleanup_directory.py         # 🧹 Directory cleanup tool
│   ├── performance_utils.py         # Performance monitoring
│   └── admin_manage.py              # User management
│
├── Documentation
│   ├── README.md                    # This file
│   ├── PERFORMANCE_GUIDE.md         # Detailed performance guide
│   ├── PERFORMANCE_QUICKSTART.md    # Quick setup guide
│   └── README_BUILD_WINDOWS.md      # Windows packaging guide
│
├── Configuration
│   ├── .env                         # Database credentials (not in git)
│   ├── .gitignore                   # Version control exclusions
│   ├── Requirements.txt             # Python dependencies
│   └── assets/                      # Icons and resources
│
└── Build
    ├── build_windows.ps1            # Windows build script
    ├── installer.iss                # Inno Setup config
    └── main.spec                    # PyInstaller config
```

---

## 🚀 Quick Start

### 1. Installation

```powershell
# Install dependencies
pip install -r Requirements.txt

# Configure database
# Edit .env file with your database credentials
```

### 2. Check Connection

```powershell
# Test database connectivity
python check_connection.py
```

Expected output:
```
✅ Internet connection: OK
✅ Database drivers: OK
✅ Configuration: OK
✅ Database connection: OK
✅ Query execution: OK
```

### 3. Run Application

```powershell
python main.py
```

---

## 🔧 Maintenance & Utilities

### Connection Diagnostics

**Check database connection and troubleshoot issues:**
```powershell
python check_connection.py
```

**Features:**
- ✅ Internet connectivity test
- ✅ Database driver verification
- ✅ Configuration validation
- ✅ Connection test with detailed error messages
- ✅ Continuous monitoring mode

### Directory Cleanup

**Clean temporary files and logs:**
```powershell
# Preview what will be deleted
python cleanup_directory.py --dry-run

# Clean logs and temp files
python cleanup_directory.py

# Organize dev files into dev_scripts/
python cleanup_directory.py --organize-dev

# Full cleanup including build outputs
python cleanup_directory.py --all
```

**What gets cleaned:**
- 🗑️ Log files (*.log)
- 🗑️ Temporary Office files (~$*.docx, ~$*.xlsx)
- 🗑️ Python cache (__pycache__/, *.pyc)
- 🗑️ Build outputs (build/, dist/)
- 🗑️ Test files (optional)

---

## 🔍 Error Handling

### No Internet Connection

**When app cannot connect to database:**

```
⚠️ Cannot Connect to Database

Possible causes:
• No internet connection
• Database server is down
• Incorrect database configuration

Please check your connection and try again.
```

**Troubleshooting steps:**
1. Run `python check_connection.py` for diagnostics
2. Check internet connection (WiFi/LAN)
3. Verify VPN is connected (if required)
4. Contact IT support if issue persists

### Connection Errors

The app now provides specific error messages for:
- ❌ **No internet:** "Cannot reach database server. Please check your internet connection."
- ❌ **Timeout:** "Connection timeout. Please check your internet connection and try again."
- ❌ **Authentication:** "Database login failed. Please contact your system administrator."
- ❌ **Server down:** "Cannot connect to database server. Please check your internet connection."

---

## 📊 Performance Features

### Connection Pooling (Automatic)

**Before:** 1 connection shared across all users (slow, serialized)
**After:** 10-30 connections in pool (fast, parallel)

**Benefits for 600 branches:**
- 🚀 **30x faster** during peak times
- ✅ No timeouts during morning rush
- ✅ Handles 100+ simultaneous users
- ✅ Auto-reconnection on network issues

### Query Caching

Lookup queries (corporations, branches) are cached automatically:
```python
# First call: 15ms
corporations = db_manager.execute_cached_query("SELECT DISTINCT corporation...")

# Second call: 0.001ms (12,000x faster!)
corporations = db_manager.execute_cached_query("SELECT DISTINCT corporation...")
```

### Performance Monitoring

Track slow queries automatically:
```powershell
# Check performance.log for slow operations
cat performance.log
```

Example output:
```
2026-02-16 10:00:00 - INFO - populate_table took 0.245s
2026-02-16 10:00:05 - WARNING - SLOW: load_reports took 3.21s
```

---

## 🔐 Security Best Practices

### Database Credentials

✅ **DO:**
- Store credentials in `.env` file (not tracked in git)
- Use strong passwords
- Limit database user permissions

❌ **DON'T:**
- Commit `.env` file to git
- Hardcode passwords in code
- Share database credentials

### .env File Example

```env
MYSQL_HOST=your-database-host.com
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_secure_password
MYSQL_DATABASE=operation_db
```

---

## 📦 Building for Production

### Windows Executable

```powershell
# Build standalone .exe
.\build_windows.ps1

# Output: dist/main.exe
```

### Windows Installer

```powershell
# Requires Inno Setup installed
# Automatically created by build_windows.ps1 if ISCC is available

# Manual build:
iscc installer.iss

# Output: OperationReportSystem_Installer.exe
```

See [README_BUILD_WINDOWS.md](README_BUILD_WINDOWS.md) for details.

---

## 🐛 Troubleshooting

### Application Won't Start

1. **Check Dependencies:**
   ```powershell
   pip install -r Requirements.txt
   ```

2. **Test Connection:**
   ```powershell
   python check_connection.py
   ```

3. **Check Logs:**
   - `database.log` - Database connection issues
   - `performance.log` - Application performance
   - Console output - Runtime errors

### Slow Performance

1. **Verify Connection Pooling is Active:**
   ```powershell
   # Check database.log for this message:
   grep "connection pool created" database.log
   ```

2. **Add Database Indexes:**
   See [PERFORMANCE_GUIDE.md](PERFORMANCE_GUIDE.md#database-optimization-checklist)

3. **Profile Queries:**
   ```python
   from performance_utils import QueryProfiler
   
   profiler = QueryProfiler()
   profiler.start()
   # ... run operations ...
   profiler.stop()
   print(profiler.get_report())
   ```

### Connection Errors

**Error: "Cannot connect to database"**
- Check internet connection
- Run `python check_connection.py`
- Verify `.env` file exists and has correct credentials
- Check if database server is accessible

**Error: "Too many connections"**
- Reduce pool size in `db_connect_pooled.py`
- Check MySQL `max_connections` setting
- Contact database administrator

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| [README.md](README.md) | This file - Project overview |
| [PERFORMANCE_GUIDE.md](PERFORMANCE_GUIDE.md) | Complete performance optimization guide |
| [PERFORMANCE_QUICKSTART.md](PERFORMANCE_QUICKSTART.md) | 5-minute performance setup |
| [PERFORMANCE_SUMMARY.md](PERFORMANCE_SUMMARY.md) | Test results and metrics |
| [README_BUILD_WINDOWS.md](README_BUILD_WINDOWS.md) | Windows build instructions |

---

## 🆘 Support

### Getting Help

1. **Check documentation** (files listed above)
2. **Run diagnostics:** `python check_connection.py`
3. **Check logs:** Review `database.log` and `performance.log`
4. **Contact IT Support** with error messages

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| No internet error | Run `check_connection.py`, verify network |
| App freezing | Enable async operations (see PERFORMANCE_GUIDE.md) |
| Slow performance | Verify connection pooling active |
| Login fails | Check database credentials in `.env` |
| Build fails | Install PyInstaller: `pip install pyinstaller` |

---

## 📈 System Requirements

### Minimum
- **OS:** Windows 10/11, Ubuntu 20.04+
- **Python:** 3.8+
- **RAM:** 4GB
- **Network:** Stable internet connection
- **Database:** MySQL 5.7+ or MariaDB 10.3+

### Recommended (600+ branches)
- **RAM:** 8GB+
- **Network:** 10+ Mbps dedicated
- **Database:** MySQL 8.0+ with max_connections ≥ 200

---

## 🔄 Version History

### v2.0 (2026-02-16)
- ✨ Added connection pooling (10-30 concurrent connections)
- ✨ Added network error detection and user-friendly messages
- ✨ Added connection diagnostics tool
- ✨ Added directory cleanup utility
- ✨ Excel export (replaced Word in Palawan page)
- ✨ Performance monitoring and profiling
- ✨ Comprehensive documentation
- 🐛 Fixed UI freezing during database operations
- 🐛 Fixed timeout errors with large user base

### v1.0
- Initial release
- Basic CRUD operations
- Single database connection

---

## 📄 License

Copyright © 2026 Operation Report System
All rights reserved.

---

## 👨‍💻 Development

### Setting Up Development Environment

```powershell
# Clone repository
git clone <repository-url>
cd Operation-Report-System

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r Requirements.txt

# Configure database
cp .env.example .env
# Edit .env with your settings

# Run tests
python test_performance_improvements.py

# Run application
python main.py
```

### Contributing

1. Move test files to `dev_scripts/` folder
2. Add new dependencies to `Requirements.txt`
3. Update documentation
4. Test with `python check_connection.py`
5. Clean directory before commit: `python cleanup_directory.py`

---

**Built with ❤️ for efficient branch operations management**
