"""
Migration script to add os_name (Operation Supervisor) column to branches table.
Run this script once to update the database schema.
"""
from db_connect_pooled import db_manager


def migrate():
    """Add os_name column to branches table"""

    # Check if column already exists
    check_query = """
        SELECT COUNT(*) as cnt
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'branches'
          AND COLUMN_NAME  = 'os_name'
    """
    result = db_manager.execute_query(check_query)

    if result and result[0]['cnt'] > 0:
        print("Column 'os_name' already exists in branches table.")
        return True

    # Add the column
    alter_query = """
        ALTER TABLE branches
        ADD COLUMN os_name VARCHAR(255) DEFAULT NULL
    """

    res = db_manager.execute_query(alter_query)
    if res is not None:
        print("Successfully added 'os_name' column to branches table.")
        return True
    else:
        print("Failed to add 'os_name' column to branches table.")
        return False


if __name__ == "__main__":
    migrate()
