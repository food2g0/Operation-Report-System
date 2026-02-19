from db_connect_pooled import db_manager

def add_missing_users_columns():
    """Add missing columns to users table"""
    
    print("Adding missing columns to users table...")
    
    # Add missing columns
    columns = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(255) AFTER password",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(255) AFTER first_name",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS corporation VARCHAR(255) AFTER last_name",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS branch VARCHAR(255) AFTER corporation",
    ]
    
    for sql in columns:
        try:
            db_manager.execute_query(sql)
            col_name = sql.split("ADD COLUMN IF NOT EXISTS ")[1].split(" ")[0]
            print(f"  ✓ Added: {col_name}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\nDone! Users table updated.")

if __name__ == "__main__":
    add_missing_users_columns()
