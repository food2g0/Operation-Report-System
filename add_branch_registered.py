"""
Migration script to add is_registered column to branches table.
Run this script once to update the database schema.
"""
from db_connect_pooled import db_manager


def migrate():
    """Add is_registered column to branches table"""
    
    # Check if column already exists
    check_query = """
        SELECT COUNT(*) as cnt 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
          AND TABLE_NAME = 'branches' 
          AND COLUMN_NAME = 'is_registered'
    """
    result = db_manager.execute_query(check_query)
    
    if result and result[0]['cnt'] > 0:
        print("Column 'is_registered' already exists in branches table.")
        return True
    
    # Add the column - default to TRUE (1) for existing branches
    alter_query = """
        ALTER TABLE branches 
        ADD COLUMN is_registered TINYINT(1) NOT NULL DEFAULT 1
    """
    
    res = db_manager.execute_query(alter_query)
    if res is not None:
        print("Successfully added 'is_registered' column to branches table.")
        print("All existing branches are marked as registered by default.")
        return True
    else:
        print("Failed to add 'is_registered' column to branches table.")
        return False


if __name__ == "__main__":
    migrate()
