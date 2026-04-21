#!/usr/bin/env python3
"""
REST API Server Setup Verification Script
Verifies that the API is properly set up and ready to run
"""

import os
import sys
import json
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ MISSING {description}: {filepath}")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'flask',
        'flask_cors',
        'jwt',
        'sqlalchemy',
        'pymysql',
    ]
    
    print("\n📦 Checking dependencies...")
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ Missing: {package}")
            missing.append(package)
    
    return len(missing) == 0, missing

def check_environment():
    """Check environment configuration"""
    print("\n⚙️  Checking environment configuration...")
    
    env_file = Path('.env')
    if env_file.exists():
        print("✓ .env file exists")
        with open('.env', 'r') as f:
            content = f.read()
            if 'API_SECRET_KEY' in content:
                print("✓ API_SECRET_KEY configured")
                return True
            else:
                print("⚠ API_SECRET_KEY not configured")
                return False
    else:
        print("✗ .env file not found")
        print("  → Use: cp .env.example .env")
        return False

def check_database():
    """Check database connectivity"""
    print("\n🗄️  Checking database connectivity...")
    
    try:
        from config import DB_CONFIG
        print(f"✓ Database config loaded")
        print(f"  Host: {DB_CONFIG.get('host')}")
        print(f"  Database: {DB_CONFIG.get('database')}")
        
        try:
            from api.services.database_service import DatabaseService
            db = DatabaseService()
            if db.check_connection():
                print("✓ Database connection successful")
                return True
            else:
                print("✗ Database connection failed")
                print("  → Check credentials in config.py")
                return False
        except Exception as e:
            print(f"✗ Database connection error: {e}")
            return False
    except Exception as e:
        print(f"✗ Error loading database config: {e}")
        return False

def check_api_files():
    """Check if all API files are created"""
    print("\n📁 Checking API files...")
    
    required_files = [
        ('api/__init__.py', 'API package init'),
        ('api/app.py', 'Flask app'),
        ('api/services/database_service.py', 'Database service'),
        ('api/services/auth_service.py', 'Auth service'),
        ('api/routes/reports_routes.py', 'Reports routes'),
        ('api/routes/users_routes.py', 'Users routes'),
        ('api/routes/data_routes.py', 'Data routes'),
        ('api/routes/transactions_routes.py', 'Transactions routes'),
        ('api_client.py', 'API client library'),
        ('run_api_server.py', 'API server entry point'),
    ]
    
    all_exist = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def check_documentation():
    """Check if documentation files exist"""
    print("\n📚 Checking documentation...")
    
    doc_files = [
        ('REST_API_SETUP.md', 'Setup guide'),
        ('REST_API_CLIENT_MIGRATION.md', 'Migration guide'),
        ('REST_API_QUICK_REFERENCE.md', 'Quick reference'),
        ('REST_API_SUMMARY.md', 'Summary'),
    ]
    
    for filepath, description in doc_files:
        check_file_exists(filepath, description)

def main():
    print("\n" + "="*60)
    print("REST API Setup Verification")
    print("="*60)
    
    results = {
        'files': check_api_files(),
        'dependencies': check_dependencies()[0],
        'environment': check_environment(),
        'database': check_database(),
    }
    
    check_documentation()
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    all_pass = all(results.values())
    
    if all_pass:
        print("\n✅ All checks passed! API is ready to run.")
        print("\nNext steps:")
        print("1. python run_api_server.py")
        print("2. Verify at: http://localhost:5000/api/v1/health")
        print("3. Read: REST_API_CLIENT_MIGRATION.md")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        print("\nFailed checks:")
        for check, passed in results.items():
            if not passed:
                print(f"  - {check}")
        
        if not results['dependencies'][0]:
            missing = results['dependencies'][1]
            print(f"\nInstall missing packages:")
            print(f"pip install {' '.join(missing)}")
        
        return 1

if __name__ == '__main__':
    sys.exit(main())
