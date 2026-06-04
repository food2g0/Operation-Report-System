"""
Maintenance Mode Manager
========================
Manages system-wide maintenance mode notifications.
Displays professional maintenance banners to clients and admins.
"""

import datetime
from typing import Dict, Optional
from api_db_manager import db_manager


def init_maintenance_table():
    """Create maintenance_mode table if it doesn't exist."""
    try:
        db_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS maintenance_mode (
                id INT AUTO_INCREMENT PRIMARY KEY,
                is_active BOOLEAN DEFAULT FALSE,
                is_blocking BOOLEAN DEFAULT FALSE,
                title VARCHAR(255) DEFAULT 'System Maintenance',
                message TEXT,
                started_at DATETIME,
                ends_at DATETIME,
                started_by VARCHAR(64),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        # Try to add is_blocking column if it doesn't exist (for existing installations)
        try:
            db_manager.execute_query("""
                ALTER TABLE maintenance_mode ADD COLUMN is_blocking BOOLEAN DEFAULT FALSE
            """)
        except:
            pass  # Column already exists
        
        return True
    except Exception as e:
        print(f"[MaintenanceMode] Failed to create table: {e}")
        return False


def is_maintenance_active() -> bool:
    """Check if maintenance mode is currently active."""
    try:
        result = db_manager.execute_query(
            "SELECT is_active FROM maintenance_mode WHERE is_active = TRUE LIMIT 1"
        )
        return len(result) > 0 if result else False
    except Exception as e:
        print(f"[MaintenanceMode] Error checking status: {e}")
        return False


def get_maintenance_info() -> Optional[Dict]:
    """Get current maintenance mode information."""
    try:
        result = db_manager.execute_query(
            "SELECT id, title, message, started_at, ends_at, started_by FROM maintenance_mode WHERE is_active = TRUE LIMIT 1"
        )
        if result:
            return result[0]
        return None
    except Exception as e:
        print(f"[MaintenanceMode] Error fetching info: {e}")
        return None


def start_maintenance(title: str = "System Maintenance", 
                     message: str = "We are performing scheduled maintenance. We'll be back soon!",
                     duration_minutes: int = 30,
                     username: str = "admin",
                     is_blocking: bool = False) -> bool:
    """
    Start maintenance mode.
    
    Args:
        title: Maintenance title
        message: Maintenance message
        duration_minutes: How long maintenance will last
        username: Who initiated it
        is_blocking: If True, clients cannot use app (full-screen block). 
                     If False, shows notification banner but app remains accessible.
    """
    try:
        now = datetime.datetime.now()
        ends_at = now + datetime.timedelta(minutes=duration_minutes)
        
        # Deactivate any existing records
        db_manager.execute_query("UPDATE maintenance_mode SET is_active = FALSE")
        
        # Insert new maintenance record
        db_manager.execute_query("""
            INSERT INTO maintenance_mode (is_active, is_blocking, title, message, started_at, ends_at, started_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (True, is_blocking, title, message, now, ends_at, username))
        
        return True
    except Exception as e:
        print(f"[MaintenanceMode] Error starting maintenance: {e}")
        return False


def stop_maintenance() -> bool:
    """Stop maintenance mode."""
    try:
        db_manager.execute_query(
            "UPDATE maintenance_mode SET is_active = FALSE WHERE is_active = TRUE"
        )
        return True
    except Exception as e:
        print(f"[MaintenanceMode] Error stopping maintenance: {e}")
        return False


def extend_maintenance(additional_minutes: int = 15) -> bool:
    """Extend maintenance duration by additional minutes."""
    try:
        result = db_manager.execute_query(
            "SELECT ends_at FROM maintenance_mode WHERE is_active = TRUE LIMIT 1"
        )
        if result:
            current_ends_at = result[0]['ends_at']
            new_ends_at = current_ends_at + datetime.timedelta(minutes=additional_minutes)
            db_manager.execute_query(
                "UPDATE maintenance_mode SET ends_at = %s WHERE is_active = TRUE",
                (new_ends_at,)
            )
            return True
        return False
    except Exception as e:
        print(f"[MaintenanceMode] Error extending maintenance: {e}")
        return False


def is_maintenance_blocking() -> bool:
    """Check if maintenance is currently BLOCKING (clients cannot access)."""
    try:
        result = db_manager.execute_query(
            "SELECT is_blocking FROM maintenance_mode WHERE is_active = TRUE AND is_blocking = TRUE LIMIT 1"
        )
        return len(result) > 0 if result else False
    except Exception as e:
        print(f"[MaintenanceMode] Error checking blocking status: {e}")
        return False
