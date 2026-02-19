import os
import time
import threading
import logging
import pymysql
from pymysql.cursors import DictCursor
from config import DB_CONFIG


class DatabaseManager:
    """
    Professional MySQL Database Manager
    - Auto connect
    - Auto reconnect
    - Idle timeout auto-close
    - Secure credential handling
    """

    def __init__(self, idle_timeout=300):
        """
        idle_timeout: seconds before DB connection is closed (default 5 mins)
        """
        self.connection = None
        self.idle_timeout = idle_timeout
        self.last_used = time.time()
        self.lock = threading.Lock()

        self.setup_logging()
        self.connect()
        self.start_idle_monitor()

    # ---------------------------------------------------
    # Logging
    # ---------------------------------------------------
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("database.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("DatabaseManager")

    # ---------------------------------------------------
    # Connection handling
    # ---------------------------------------------------
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = pymysql.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database'],
                port=DB_CONFIG['port'],
                cursorclass=DictCursor,
                autocommit=False,
                connect_timeout=10,
                charset="utf8mb4"
            )
            self.last_used = time.time()
            self.logger.info("MySQL connected successfully")
            return True

        except Exception as e:
            self.connection = None
            self.logger.error(f"MySQL connection failed: {e}")
            return False

    def reconnect_if_needed(self):
        """Reconnect if connection is lost"""
        if not self.connection:
            return self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.last_used = time.time()
            return True

        except Exception:
            self.logger.warning("MySQL connection lost — reconnecting")
            return self.connect()

    # ---------------------------------------------------
    # Idle monitor (auto close)
    # ---------------------------------------------------
    def start_idle_monitor(self):
        def monitor():
            while True:
                time.sleep(30)
                with self.lock:
                    if (
                        self.connection
                        and time.time() - self.last_used > self.idle_timeout
                    ):
                        try:
                            self.logger.info("Idle timeout reached — closing DB connection")
                            self.connection.close()
                            self.connection = None
                        except Exception:
                            pass

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    # ---------------------------------------------------
    # Query execution
    # ---------------------------------------------------
    def execute_query(self, query, params=None):
        """Execute SELECT / INSERT / UPDATE / DELETE"""
        with self.lock:
            if not self.reconnect_if_needed():
                return None

            try:
                with self.connection.cursor() as cursor:
                    self.last_used = time.time()
                    cursor.execute(query, params)

                    if query.strip().upper().startswith("SELECT"):
                        return cursor.fetchall()
                    else:
                        self.connection.commit()
                        return cursor.rowcount

            except Exception as e:
                self.logger.error(f"Query failed: {e}")
                try:
                    self.connection.rollback()
                except Exception:
                    pass
                return None

    def execute_query_with_exception(self, query, params=None):
        """Same as execute_query but returns (result, exception)"""
        with self.lock:
            if not self.reconnect_if_needed():
                return None, Exception("Database connection failed")

            try:
                with self.connection.cursor() as cursor:
                    self.last_used = time.time()
                    cursor.execute(query, params)

                    if query.strip().upper().startswith("SELECT"):
                        result = cursor.fetchall()
                    else:
                        self.connection.commit()
                        result = cursor.rowcount

                    return result, None

            except Exception as e:
                self.logger.error(f"Query failed: {e}")
                try:
                    self.connection.rollback()
                except Exception:
                    pass
                return None, e

    # ---------------------------------------------------
    # Connection test
    # ---------------------------------------------------
    def test_connection(self):
        """Test DB connection"""
        if not self.reconnect_if_needed():
            return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS test")
                result = cursor.fetchone()
                return result and result["test"] == 1
        except Exception:
            return False

    # ---------------------------------------------------
    # Shutdown
    # ---------------------------------------------------
    def shutdown(self):
        """Call this when app exits"""
        with self.lock:
            if self.connection:
                try:
                    self.connection.close()
                    self.logger.info("DB connection closed on app exit")
                except Exception:
                    pass
                self.connection = None


# ---------------------------------------------------
# Global instance (recommended)
# ---------------------------------------------------
db_manager = DatabaseManager()

# ---------------------------------------------------
# Standalone test
# ---------------------------------------------------
if __name__ == "__main__":
    print("Testing database connection...")
    if db_manager.test_connection():
        print("✅ Database connection OK")
    else:
        print("❌ Database connection FAILED")
