"""
Error Tracking & Audit System
Tracks exceptions, audit trails, and system events in a SQLite database.
"""

import os
import sys
import json
import sqlite3
import logging
import threading
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

# Create data directory
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

ERROR_DB = DATA_DIR / "errors.db"
AUDIT_DB = DATA_DIR / "audit.db"


class ErrorTracker:
    """Track exceptions and errors."""

    def __init__(self, db_path: Path = ERROR_DB):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    message TEXT,
                    stack_trace TEXT,
                    source TEXT,
                    remote_ip TEXT,
                    resolved INTEGER DEFAULT 0,
                    resolved_at TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_errors_timestamp ON errors(timestamp DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_errors_resolved ON errors(resolved)
            """)
            conn.commit()

    def track(self, exc: Exception, source: str = "unknown", remote_ip: str = None) -> int:
        """Record an exception."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                error_id = conn.execute("""
                    INSERT INTO errors (timestamp, error_type, message, stack_trace, source, remote_ip)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    datetime.utcnow().isoformat(),
                    type(exc).__name__,
                    str(exc),
                    traceback.format_exc(),
                    source,
                    remote_ip
                )).lastrowid
                conn.commit()
                return error_id

    def get_recent(self, hours: int = 24, unresolved_only: bool = True) -> List[Dict]:
        """Get recent errors."""
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        query = "SELECT * FROM errors WHERE timestamp > ? "
        params = [cutoff]

        if unresolved_only:
            query += "AND resolved = 0 "

        query += "ORDER BY timestamp DESC LIMIT 100"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_counts(self, hours: int = 24) -> Dict[str, int]:
        """Get error counts by type."""
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT error_type, COUNT(*) as count
                FROM errors
                WHERE timestamp > ? AND resolved = 0
                GROUP BY error_type
                ORDER BY count DESC
            """, [cutoff]).fetchall()
            return {row['error_type']: row['count'] for row in rows}

    def resolve(self, error_id: int, notes: str = None):
        """Mark an error as resolved."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE errors
                    SET resolved = 1, resolved_at = ?, notes = ?
                    WHERE id = ?
                """, (datetime.utcnow().isoformat(), notes, error_id))
                conn.commit()


class AuditLogger:
    """Track all database writes (INSERT, UPDATE, DELETE) with user and timestamp."""

    def __init__(self, db_path: Path = AUDIT_DB):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Create audit table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    table_name TEXT,
                    sql_query TEXT,
                    affected_rows INTEGER,
                    user TEXT,
                    remote_ip TEXT,
                    status TEXT,
                    error_msg TEXT,
                    duration_ms REAL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name)
            """)
            conn.commit()

    def log(
        self,
        operation: str,
        table_name: str,
        sql_query: str,
        user: str = None,
        remote_ip: str = None,
        affected_rows: int = None,
        status: str = "success",
        error_msg: str = None,
        duration_ms: float = None
    ):
        """Log a database operation."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO audit_log
                    (timestamp, operation, table_name, sql_query, user, remote_ip,
                     affected_rows, status, error_msg, duration_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.utcnow().isoformat(),
                    operation,
                    table_name,
                    sql_query[:500],  # Truncate long queries
                    user,
                    remote_ip,
                    affected_rows,
                    status,
                    error_msg[:500] if error_msg else None,
                    duration_ms
                ))
                conn.commit()

    def get_recent(self, hours: int = 24, user: str = None, table_name: str = None) -> List[Dict]:
        """Get recent audit entries."""
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        query = "SELECT * FROM audit_log WHERE timestamp > ? "
        params = [cutoff]

        if user:
            query += "AND user = ? "
            params.append(user)

        if table_name:
            query += "AND table_name = ? "
            params.append(table_name)

        query += "ORDER BY timestamp DESC LIMIT 200"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_user_activity(self, user: str, hours: int = 24) -> List[Dict]:
        """Get all activity for a specific user."""
        return self.get_recent(hours=hours, user=user)


# Global instances
error_tracker = ErrorTracker()
audit_logger = AuditLogger()


def log_exception(exc: Exception, source: str = "unknown", remote_ip: str = None) -> int:
    """Convenience function to log an exception."""
    return error_tracker.track(exc, source=source, remote_ip=remote_ip)


def log_audit(operation: str, table_name: str, sql: str, **kwargs):
    """Convenience function to log an audit event."""
    audit_logger.log(operation, table_name, sql, **kwargs)
