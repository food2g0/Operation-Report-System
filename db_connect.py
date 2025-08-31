import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()


class DatabaseManager:
    """Database manager for handling MySQL connection - Same structure as original psycopg2 code"""

    def __init__(self):
        self.connection = None
        self.setup_logging()
        self.connect()

    def setup_logging(self):
        """Setup logging for database operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('database.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def connect(self):
        """Establish MySQL database connection with retry logic"""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Get connection parameters from environment or use XAMPP defaults
                host = os.getenv("MYSQL_HOST", "localhost")
                port = int(os.getenv("MYSQL_PORT", 3306))
                user = os.getenv("MYSQL_USER", "root")
                password = os.getenv("MYSQL_PASSWORD", "")
                database = os.getenv("MYSQL_DATABASE", "operation_db")

                self.logger.info(f"Attempting MySQL connection to {user}@{host}:{port}/{database}")

                # Connect using PyMySQL (similar interface to psycopg2)
                self.connection = pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database,
                    cursorclass=DictCursor,  # Similar to RealDictCursor in psycopg2
                    autocommit=False,
                    connect_timeout=30,
                    charset='utf8mb4'
                )

                self.logger.info("Database connection established successfully")
                return True

            except Exception as e:
                retry_count += 1
                self.logger.error(f"MySQL connection failed (attempt {retry_count}): {e}")

                if "Can't connect to MySQL server" in str(e):
                    self.logger.error("MySQL server is not running! Please start MySQL in XAMPP Control Panel")
                elif "Access denied" in str(e):
                    self.logger.error("Access denied! Check your username and password")
                elif "Unknown database" in str(e):
                    self.logger.error(f"Database '{database}' doesn't exist!")

                if retry_count >= max_retries:
                    self.connection = None
                    return False

        return False

    def reconnect_if_needed(self):
        """Check connection and reconnect if necessary"""
        try:
            if not self.connection or not self.connection.open:
                return self.connect()

            # Test the connection (similar to psycopg2 style)
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except:
            return self.connect()

    def test_connection(self):
        """Test database connection"""
        try:
            if not self.reconnect_if_needed():
                return False

            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                return result and result["test"] == 1
        except:
            return False

    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        try:
            if not self.reconnect_if_needed():
                return None

            with self.connection.cursor() as cursor:
                cursor.execute(query, params)

                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                else:
                    self.connection.commit()
                    result = cursor.rowcount

                return result

        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            if self.connection:
                self.connection.rollback()
            return None

    def close(self):
        """Close database connection"""
        if self.connection:
            try:
                self.connection.close()
                self.logger.info("Database connection closed")
            except Exception as e:
                self.logger.error(f"Error closing connection: {e}")


# Global database manager instance
db_manager = DatabaseManager()

if __name__ == "__main__":
    print("Testing MySQL database connection...")
    if db_manager.test_connection():
        print("✅ MySQL database connection successful")

        # Test with a simple query
        try:
            result = db_manager.execute_query("SHOW DATABASES")
            if result:
                print("\nAvailable databases:")
                for db in result:
                    print(f"  - {db['Database']}")
        except Exception as e:
            print(f"Error listing databases: {e}")
    else:
        print("❌ MySQL database connection failed")
        print("\nTroubleshooting tips:")
        print("1. Make sure XAMPP is running")
        print("2. Start MySQL service in XAMPP Control Panel")
        print("3. Check if MySQL is running on port 3306")
        print("4. Verify your database credentials")