#!/usr/bin/env python3
"""
Migration script to add sub_corporation_id column to branches table
Run: python migrate_add_sub_corporation.py
"""
from db_connect_pooled import db_manager

def migrate_add_sub_corp_column():
    """Add sub_corporation_id column to branches table if it doesn't exist"""
    
    # Check if column already exists
    result = db_manager.execute_query("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'branches' 
        AND COLUMN_NAME = 'sub_corporation_id'
    """)
    
    if result and len(result) > 0:
        print("✓ Column 'sub_corporation_id' already exists in branches table")
        return True
    
    try:
        # Add the column
        db_manager.execute_query("""
            ALTER TABLE branches 
            ADD COLUMN sub_corporation_id INT DEFAULT NULL
        """)
        print("✓ Successfully added 'sub_corporation_id' column to branches table")
        
        # Optionally add foreign key constraint (commented out for now to avoid strict constraints)
        # db_manager.execute_query("""
        #     ALTER TABLE branches 
        #     ADD CONSTRAINT fk_sub_corp FOREIGN KEY (sub_corporation_id) 
        #     REFERENCES corporations(id) ON DELETE SET NULL
        # """)
        # print("✓ Added foreign key constraint")
        
        return True
    except Exception as e:
        print(f"✗ Error adding column: {e}")
        return False

if __name__ == '__main__':
    print("Migrating branches table...")
    if db_manager.test_connection():
        if migrate_add_sub_corp_column():
            print("\n✓ Migration completed successfully!")
        else:
            print("\n✗ Migration failed!")
    else:
        print("✗ Cannot connect to database")
