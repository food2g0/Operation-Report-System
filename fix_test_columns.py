"""
Script to add missing 'test' and 'test_lotes' columns to database tables.
Run this to fix the "Unknown column 'test'" error.
"""
from db_connect_pooled import db_manager

def main():
    # Test connection
    if not db_manager.test_connection():
        print('ERROR: Cannot connect to database')
        return False

    print('Connected to database')

    # Check what columns exist in daily_reports_brand_a
    cols = db_manager.execute_query(
        "SELECT COLUMN_NAME FROM information_schema.columns WHERE table_name = %s AND table_schema = DATABASE()",
        ['daily_reports_brand_a']
    )
    existing = [c['COLUMN_NAME'] for c in cols]
    print(f'Found {len(existing)} columns in daily_reports_brand_a')
    print('Has test column:', 'test' in existing)
    print('Has test_lotes column:', 'test_lotes' in existing)

    # Try to add the columns to both tables
    tables = ['daily_reports', 'daily_reports_brand_a']
    
    for table in tables:
        print(f'\nProcessing {table}...')
        
        # Add test column
        try:
            sql = f"ALTER TABLE `{table}` ADD COLUMN `test` DECIMAL(15,2) DEFAULT 0"
            db_manager.execute_query(sql)
            print(f'  Added test column')
        except Exception as e:
            if '1060' in str(e) or 'Duplicate' in str(e):
                print(f'  test column already exists')
            else:
                print(f'  ERROR adding test: {e}')
        
        # Add test_lotes column
        try:
            sql = f"ALTER TABLE `{table}` ADD COLUMN `test_lotes` SMALLINT DEFAULT 0"
            db_manager.execute_query(sql)
            print(f'  Added test_lotes column')
        except Exception as e:
            if '1060' in str(e) or 'Duplicate' in str(e):
                print(f'  test_lotes column already exists')
            else:
                print(f'  ERROR adding test_lotes: {e}')

    # Verify columns were added
    print('\n--- Verification ---')
    cols = db_manager.execute_query(
        "SELECT COLUMN_NAME FROM information_schema.columns WHERE table_name = %s AND table_schema = DATABASE()",
        ['daily_reports_brand_a']
    )
    existing = [c['COLUMN_NAME'] for c in cols]
    print('Has test column now:', 'test' in existing)
    print('Has test_lotes column now:', 'test_lotes' in existing)
    
    print('\nDone!')
    return True

if __name__ == '__main__':
    main()
