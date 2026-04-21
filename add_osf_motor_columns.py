#!/usr/bin/env python3
"""
Migration script to add osf_motor and osf_motor_lotes columns to daily reporting tables.
"""

from db_connect_pooled import db_manager

def add_osf_motor_columns():
    """Add osf_motor and osf_motor_lotes columns to all daily report tables."""
    
    tables = [
        "daily_reports_brand_a",
        "daily_reports",  # Brand B
    ]
    
    print("=" * 60)
    print("Adding OSF Motor columns to database tables...")
    print("=" * 60)
    
    if not db_manager.test_connection():
        print("❌ Cannot connect to database!")
        return False
    
    for table in tables:
        print(f"\n📍 Processing: {table}")
        
        # Check if table exists
        try:
            exists = db_manager.execute_query(
                "SELECT COUNT(*) as cnt FROM information_schema.tables "
                "WHERE table_schema = DATABASE() AND table_name = %s",
                (table,)
            )
            if not exists or exists[0]['cnt'] == 0:
                print(f"   ⚠️  Table {table} doesn't exist. Skipping...")
                continue
        except Exception as e:
            print(f"   ❌ Error checking table: {e}")
            continue
        
        # Add osf_motor column
        try:
            check = db_manager.execute_query(
                "SELECT COUNT(*) as cnt FROM information_schema.columns "
                "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = 'osf_motor'",
                (table,)
            )
            
            if check and check[0]['cnt'] > 0:
                print(f"   ✓ osf_motor column already exists")
            else:
                db_manager.execute_query(
                    f"ALTER TABLE `{table}` ADD COLUMN `osf_motor` DECIMAL(15,2) DEFAULT 0"
                )
                print(f"   ✓ Added osf_motor column")
        except Exception as e:
            print(f"   ❌ Error adding osf_motor: {e}")
        
        # Add osf_motor_lotes column
        try:
            check = db_manager.execute_query(
                "SELECT COUNT(*) as cnt FROM information_schema.columns "
                "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = 'osf_motor_lotes'",
                (table,)
            )
            
            if check and check[0]['cnt'] > 0:
                print(f"   ✓ osf_motor_lotes column already exists")
            else:
                db_manager.execute_query(
                    f"ALTER TABLE `{table}` ADD COLUMN `osf_motor_lotes` SMALLINT DEFAULT 0"
                )
                print(f"   ✓ Added osf_motor_lotes column")
        except Exception as e:
            print(f"   ❌ Error adding osf_motor_lotes: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Migration complete!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    add_osf_motor_columns()
