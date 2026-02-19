"""
Migration script to add variance_status column to daily_reports tables.
This column tracks whether an entry has short, over, or balanced cash variance.

Run this script once to add the column to both tables.
"""

from db_connect_pooled import db_manager


def add_variance_status_column():
    """Add variance_status column to daily_reports and daily_reports_brand_a tables"""
    
    tables = ['daily_reports', 'daily_reports_brand_a']
    
    for table in tables:
        try:
            # Check if column already exists
            check_query = f"""
                SELECT COUNT(*) as cnt
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = '{table}'
                  AND COLUMN_NAME = 'variance_status'
            """
            result = db_manager.execute_query(check_query)
            
            if result and result[0].get('cnt', 0) > 0:
                print(f"✓ Column 'variance_status' already exists in {table}")
                continue
            
            # Add the column
            alter_query = f"""
                ALTER TABLE {table}
                ADD COLUMN variance_status VARCHAR(20) DEFAULT 'balanced'
                COMMENT 'Tracks cash variance status: balanced, short, or over'
            """
            db_manager.execute_query(alter_query)
            print(f"✓ Added 'variance_status' column to {table}")
            
            # Update existing records based on cash_result
            update_query = f"""
                UPDATE {table}
                SET variance_status = CASE
                    WHEN ABS(cash_result) < 0.01 THEN 'balanced'
                    WHEN cash_result > 0 THEN 'over'
                    ELSE 'short'
                END
                WHERE variance_status IS NULL OR variance_status = ''
            """
            rows = db_manager.execute_query(update_query)
            print(f"✓ Updated existing records in {table} (affected rows: {rows})")
            
            # Add index for faster filtering
            try:
                index_query = f"""
                    ALTER TABLE {table}
                    ADD INDEX idx_variance_status (variance_status)
                """
                db_manager.execute_query(index_query)
                print(f"✓ Added index on variance_status for {table}")
            except Exception as idx_err:
                if "Duplicate key name" in str(idx_err):
                    print(f"✓ Index on variance_status already exists for {table}")
                else:
                    print(f"⚠ Could not add index for {table}: {idx_err}")
            
        except Exception as e:
            print(f"✗ Error processing {table}: {e}")
            continue
    
    print("\n✓ Migration completed!")


if __name__ == "__main__":
    print("=" * 50)
    print("Adding variance_status column to daily_reports tables")
    print("=" * 50)
    add_variance_status_column()
