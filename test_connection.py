import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def test_environment_variables():

    print("=== Checking Environment Variables ===")


    required_vars = [
        'DB_HOST',
        'DB_USER',
        'DB_PASSWORD',
        'DB_NAME'
    ]

    optional_vars = {
        'DB_PORT': '3306'
    }

    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if value is not None:  # allow empty password
            if 'PASSWORD' in var:
                print(f"✓ {var}: [SET]")
            else:
                print(f"✓ {var}: {value if value != '' else '[EMPTY]'}")
        else:
            print(f"✗ {var}: NOT SET")
            missing_vars.append(var)

    for var, default in optional_vars.items():
        value = os.getenv(var, default)
        print(f"✓ {var}: {value}")

    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False

    print("\n✅ All environment variables are set")
    return True


def test_packages():
    """Test if required packages are installed"""
    print("\n=== Checking Required Packages ===")

    required_packages = [
        ('sqlalchemy', 'SQLAlchemy'),
        ('pymysql', 'PyMySQL'),
    ]

    missing_packages = []
    failed_packages = []

    for package, name in required_packages:
        try:
            module = __import__(package)
            # Get version if available
            version = getattr(module, '__version__', 'unknown')
            print(f"✓ {name}: Installed (version: {version})")
        except ImportError:
            print(f"✗ {name}: NOT INSTALLED")
            missing_packages.append(name)
        except Exception as e:
            print(f"⚠️  {name}: Installed but has issues - {str(e)}")
            failed_packages.append(name)

    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install missing packages with:")
        print("pip install cloud-sql-python-connector[pymysql] sqlalchemy google-auth")
        return False

    if failed_packages:
        print(f"\n⚠️  Packages with issues: {', '.join(failed_packages)}")
        print("Try reinstalling these packages:")
        print("pip uninstall sqlalchemy")
        print("pip install 'sqlalchemy>=1.4,<2.1'")
        return False

    print("\n✅ All required packages are installed")
    return True


def test_database_connection():
    """Test the actual database connection"""
    print("\n=== Testing Database Connection ===")

    import pymysql

    try:
        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", 3306))
        user = os.getenv("DB_USER", "root")
        password = os.getenv("DB_PASSWORD", "")
        db_name = os.getenv("DB_NAME", "operation_db")

        print(f"Connecting to MySQL at {host}:{port}, user={user}, db={db_name}")

        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name
        )

        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ Database connection successful! MySQL version: {version[0]}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False



def show_setup_instructions():
    """Show setup instructions if tests fail"""
    print("\n=== Setup Instructions ===")
    print("""
1. Create a .env file in your project directory with:
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=
   DB_NAME=operation_db

   ⚠️ If your MySQL root has a password, put it after DB_PASSWORD.
   Example: DB_PASSWORD=mysecret

2. Or set environment variables in your system:
   Windows (Command Prompt):
     set DB_HOST=localhost
     set DB_PORT=3306
     set DB_USER=root
     set DB_PASSWORD=
     set DB_NAME=operation_db

   Linux/Mac (bash/zsh):
     export DB_HOST=localhost
     export DB_PORT=3306
     export DB_USER=root
     export DB_PASSWORD=
     export DB_NAME=operation_db

3. Make sure MySQL is running in XAMPP:
   - Open XAMPP Control Panel
   - Start Apache and MySQL
   - Access phpMyAdmin at http://localhost/phpmyadmin

4. Create the database if it doesn’t exist:
   In phpMyAdmin or MySQL CLI, run:
     CREATE DATABASE operation_db;

5. Install required Python packages:
   pip install sqlalchemy pymysql

6. Re-run this script to test the connection.
""")



def main():
    """Run all tests"""
    print("🔍 Testing Cloud SQL Setup\n")

    # Test environment variables
    env_ok = test_environment_variables()

    # Test packages
    packages_ok = test_packages()

    # Test database connection (only if previous tests pass)
    db_ok = False
    if env_ok and packages_ok:
        db_ok = test_database_connection()

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Environment Variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Required Packages: {'✅ PASS' if packages_ok else '❌ FAIL'}")
    print(f"Database Connection: {'✅ PASS' if db_ok else '❌ FAIL'}")

    if env_ok and packages_ok and db_ok:
        print("\n🎉 All tests passed! You're ready to use the application.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please check the setup instructions.")
        show_setup_instructions()
        return False


# This is the key addition - actually call main() when script is run
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)