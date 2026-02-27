"""
Improved Database Manager with Connection Pooling
This version uses SQLAlchemy connection pooling for better performance and concurrency.

To migrate:
1. Install sqlalchemy (already in Requirements.txt)
2. Replace: from db_connect import db_manager
   With:     from db_connect_pooled import db_manager
3. All execute_query() calls remain compatible
"""
import os
import time
import threading
import logging
from sqlalchemy import create_engine, text, pool
from sqlalchemy.engine import Engine
from config import DB_CONFIG
from functools import lru_cache
from typing import List, Dict, Any, Optional, Tuple


class DatabaseManagerPooled:
    """
    High-performance MySQL Database Manager with connection pooling
    - Connection pooling (10-30 concurrent connections)
    - Auto-reconnect with pre-ping
    - Compatible with existing execute_query() calls
    - LRU cache for lookup queries
    - Auto-disconnect after 5 minutes of inactivity
    - Auto-reconnect when user performs action
    """

    def __init__(self, idle_timeout=300):
        """
        idle_timeout: seconds before DB connection is closed (default 5 mins)
        """
        self.engine: Optional[Engine] = None
        self.idle_timeout = idle_timeout
        self.last_used = time.time()
        self.lock = threading.Lock()
        self._is_disconnected_for_idle = False
        
        self.setup_logging()
        self.connect()
        self.start_idle_monitor()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("database.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("DatabaseManagerPooled")

    def connect(self):
        """Establish connection pool using SQLAlchemy"""
        try:
            connection_string = (
                f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
                f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
                f"/{DB_CONFIG['database']}?charset=utf8mb4"
            )

            self.engine = create_engine(
                connection_string,
                poolclass=pool.QueuePool,
                pool_size=10,           # Keep 10 connections open
                max_overflow=20,        # Allow up to 30 total connections
                pool_recycle=3600,      # Recycle connections every hour
                pool_pre_ping=True,     # Test connection before each use
                echo=False,             # Set to True for SQL debugging
                connect_args={
                    'connect_timeout': 10
                }
            )
            
            # Test the connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.last_used = time.time()
            self._is_disconnected_for_idle = False
            self.logger.info("MySQL connection pool created successfully")
            return True

        except ImportError as e:
            self.engine = None
            self.logger.error(f"Missing database driver: {e}")
            return False
        except Exception as e:
            self.engine = None
            error_msg = str(e).lower()
            
            # Categorize errors for better user feedback
            if "can't connect" in error_msg or "connection refused" in error_msg:
                self.logger.error(f"❌ Cannot connect to database server. Check internet connection or server status: {e}")
            elif "access denied" in error_msg or "authentication" in error_msg:
                self.logger.error(f"❌ Database authentication failed. Check username/password in .env file: {e}")
            elif "unknown database" in error_msg:
                self.logger.error(f"❌ Database does not exist. Check database name in .env file: {e}")
            elif "timeout" in error_msg or "timed out" in error_msg:
                self.logger.error(f"❌ Connection timeout. Check internet connection and firewall settings: {e}")
            elif "name resolution" in error_msg or "getaddrinfo failed" in error_msg:
                self.logger.error(f"❌ Cannot resolve database hostname. Check internet connection: {e}")
            else:
                self.logger.error(f"❌ MySQL connection pool failed: {e}")
            
            return False

    def get_user_friendly_error(self, exception: Exception) -> str:
        """Convert technical database errors to user-friendly messages"""
        error_msg = str(exception).lower()
        
        if "can't connect" in error_msg or "connection refused" in error_msg:
            return "Cannot connect to database server. Please check your internet connection."
        elif "access denied" in error_msg or "authentication" in error_msg:
            return "Database login failed. Please contact your system administrator."
        elif "unknown database" in error_msg:
            return "Database configuration error. Please contact your system administrator."
        elif "timeout" in error_msg or "timed out" in error_msg:
            return "Connection timeout. Please check your internet connection and try again."
        elif "name resolution" in error_msg or "getaddrinfo failed" in error_msg:
            return "Cannot reach database server. Please check your internet connection."
        elif "lost connection" in error_msg or "server has gone away" in error_msg:
            return "Lost connection to database. Please check your internet connection and try again."
        elif "too many connections" in error_msg:
            return "Database server is busy. Please try again in a moment."
        else:
            return f"Database error occurred. Please try again or contact support."

    # ---------------------------------------------------
    # Idle monitor (auto disconnect after 5 minutes)
    # ---------------------------------------------------
    def start_idle_monitor(self):
        """Start background thread to monitor idle time and disconnect"""
        def monitor():
            while True:
                time.sleep(30)  # Check every 30 seconds
                with self.lock:
                    if (
                        self.engine
                        and time.time() - self.last_used > self.idle_timeout
                    ):
                        try:
                            self.logger.info(f"Idle timeout ({self.idle_timeout}s) reached — disconnecting from database")
                            self.engine.dispose()
                            self.engine = None
                            self._is_disconnected_for_idle = True
                        except Exception as e:
                            self.logger.error(f"Error during idle disconnect: {e}")

        thread = threading.Thread(target=monitor, daemon=True, name="IdleMonitor")
        thread.start()
        self.logger.info(f"Idle monitor started (timeout: {self.idle_timeout}s)")

    def reconnect_if_needed(self) -> bool:
        """Reconnect if connection was closed due to idle timeout or lost"""
        if not self.engine:
            if self._is_disconnected_for_idle:
                self.logger.info("Reconnecting after idle disconnect...")
            return self.connect()
        
        # Test if connection is still alive
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            self.logger.warning("Connection lost — reconnecting...")
            return self.connect()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[Any]:
        """
        Execute SELECT / INSERT / UPDATE / DELETE
        Compatible with old db_manager.execute_query() calls
        
        Returns:
        - For SELECT: List of dicts (rows)
        - For INSERT/UPDATE/DELETE: Number of affected rows
        - On error: None
        """
        with self.lock:
            # Auto-reconnect if disconnected
            if not self.reconnect_if_needed():
                self.logger.error("Failed to connect to database")
                return None

            self.last_used = time.time()  # Update activity timestamp

        try:
            with self.engine.connect() as conn:
                # Convert tuple params to dict format for SQLAlchemy
                if params and isinstance(params, (tuple, list)):
                    # Convert %s placeholders to :param0, :param1, etc.
                    modified_query = query
                    param_dict = {}
                    for i, param_value in enumerate(params):
                        param_name = f"param{i}"
                        modified_query = modified_query.replace("%s", f":{param_name}", 1)
                        param_dict[param_name] = param_value
                    result = conn.execute(text(modified_query), param_dict)
                else:
                    result = conn.execute(text(query), params or {})
                
                if query.strip().upper().startswith("SELECT"):
                    # Return list of dicts (compatible with old code)
                    return [dict(row._mapping) for row in result]
                else:
                    conn.commit()
                    return result.rowcount

        except Exception as e:
            error_msg = str(e).lower()
            
            # Categorize and log specific errors
            if any(keyword in error_msg for keyword in ["can't connect", "connection refused", "timeout", "timed out", "lost connection", "name resolution"]):
                self.logger.error(f"Network/Connection error: {e}")
            else:
                self.logger.error(f"Query failed: {e}\nQuery: {query}\nParams: {params}")
            
            return None

    def execute_query_with_exception(self, query: str, params: Optional[tuple] = None) -> Tuple[Optional[Any], Optional[Exception]]:
        """
        Same as execute_query but returns (result, exception)
        Compatible with old code that uses this method
        """
        with self.lock:
            # Auto-reconnect if disconnected
            if not self.reconnect_if_needed():
                return None, Exception("Failed to connect to database")

            self.last_used = time.time()  # Update activity timestamp

        try:
            with self.engine.connect() as conn:
                # Convert tuple params to dict format for SQLAlchemy
                if params and isinstance(params, (tuple, list)):
                    # Convert %s placeholders to :param0, :param1, etc.
                    modified_query = query
                    param_dict = {}
                    for i, param_value in enumerate(params):
                        param_name = f"param{i}"
                        modified_query = modified_query.replace("%s", f":{param_name}", 1)
                        param_dict[param_name] = param_value
                    result = conn.execute(text(modified_query), param_dict)
                else:
                    result = conn.execute(text(query), params or {})
                
                if query.strip().upper().startswith("SELECT"):
                    data = [dict(row._mapping) for row in result]
                    return data, None
                else:
                    conn.commit()
                    return result.rowcount, None

        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            return None, e

    @lru_cache(maxsize=128)
    def execute_cached_query(self, query: str, params_tuple: Optional[tuple] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a SELECT query with LRU caching
        Use for lookup data that doesn't change often (corporations, branches, etc.)
        
        Example:
            # Cache corporation list for 128 unique queries
            corps = db_manager.execute_cached_query("SELECT DISTINCT corporation FROM daily_reports ORDER BY corporation")
        """
        if not query.strip().upper().startswith("SELECT"):
            self.logger.warning("Cached queries only support SELECT statements")
            return self.execute_query(query, params_tuple)
        
        return self.execute_query(query, params_tuple)

    def clear_cache(self):
        """Clear the query cache"""
        self.execute_cached_query.cache_clear()
        self.logger.info("Query cache cleared")

    def execute_many(self, query: str, params_list: List[tuple], chunk_size: int = 100) -> Optional[int]:
        """
        Execute the same query with multiple parameter sets in batched transactions.
        Much faster than calling execute_query() in a loop.
        
        Args:
            query: SQL query with %s placeholders
            params_list: List of tuples, each containing parameters for one execution
            chunk_size: Number of operations per transaction (default 100, good for 600+ rows)
            
        Returns:
            Total number of affected rows, or None on error
        """
        if not params_list:
            return 0
            
        with self.lock:
            if not self.reconnect_if_needed():
                self.logger.error("Failed to connect to database")
                return None
            self.last_used = time.time()

        try:
            # Convert %s placeholders to :param0, :param1, etc.
            modified_query = query
            placeholder_count = query.count("%s")
            for i in range(placeholder_count):
                modified_query = modified_query.replace("%s", f":param{i}", 1)
            
            # Convert list of tuples to list of dicts
            param_dicts = []
            for params in params_list:
                param_dict = {f"param{i}": val for i, val in enumerate(params)}
                param_dicts.append(param_dict)
            
            # Execute in chunks to avoid timeouts with 600+ rows
            total_rows = 0
            for i in range(0, len(param_dicts), chunk_size):
                chunk = param_dicts[i:i + chunk_size]
                with self.engine.connect() as conn:
                    for param_dict in chunk:
                        result = conn.execute(text(modified_query), param_dict)
                        total_rows += result.rowcount
                    conn.commit()
            
            return total_rows

        except Exception as e:
            self.logger.error(f"Batch query failed: {e}\nQuery: {query}")
            return None

    def test_connection(self) -> bool:
        """Test database connection (auto-reconnects if needed)"""
        with self.lock:
            if not self.reconnect_if_needed():
                return False
            self.last_used = time.time()
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 AS test"))
                row = result.fetchone()
                return row and row[0] == 1
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    def get_connection_status(self) -> dict:
        """Get current connection status for UI display"""
        idle_seconds = time.time() - self.last_used
        return {
            'connected': self.engine is not None,
            'idle_seconds': round(idle_seconds, 1),
            'idle_timeout': self.idle_timeout,
            'will_disconnect_in': max(0, round(self.idle_timeout - idle_seconds, 1)) if self.engine else 0
        }

    def shutdown(self):
        """Dispose of the connection pool"""
        if self.engine:
            try:
                self.engine.dispose()
                self.logger.info("Connection pool disposed")
            except Exception as e:
                self.logger.error(f"Error disposing engine: {e}")
            finally:
                self.engine = None


# Global instance (compatible with old code)
db_manager = DatabaseManagerPooled()


if __name__ == "__main__":
    print("Testing database connection pool...")
    if db_manager.test_connection():
        print("✅ Database connection pool OK")
        
        # Test a simple query
        result = db_manager.execute_query("SELECT DATABASE() as db_name")
        if result:
            print(f"✅ Connected to database: {result[0]['db_name']}")
    else:
        print("❌ Database connection pool FAILED")
