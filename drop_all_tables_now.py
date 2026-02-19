from db_connect_pooled import db_manager

def clear_all_data():
    """Clear all data from all tables (TRUNCATE)"""
    
    print("=" * 60)
    print("CLEAR ALL DATA FROM TABLES")
    print("=" * 60)
    
    # Disable foreign key checks
    db_manager.execute_query("SET FOREIGN_KEY_CHECKS = 0")
    
    # Truncate all tables (removes data, keeps structure)
    tables = [
        "daily_reports_summary",
        "payable_tbl",
        "daily_reports_brand_a",
        "daily_reports",
        "users",
        "branches",
        "corporations"
    ]
    
    print("\nClearing data from tables...")
    for table in tables:
        try:
            query = f"TRUNCATE TABLE `{table}`"
            db_manager.execute_query(query)
            print(f"  ✓ Cleared data from: {table}")
        except Exception as e:
            print(f"  ✗ Error clearing {table}: {e}")
    
    # Re-enable foreign key checks
    db_manager.execute_query("SET FOREIGN_KEY_CHECKS = 1")
    
    print("\n" + "=" * 60)
    print("ALL DATA CLEARED!")
    print("=" * 60)
    print("\nTables still exist - only data removed.")
    print("Now you can restore from your backup.")

if __name__ == "__main__":
    clear_all_data()
