#!/usr/bin/env python3
"""
Clear All Data Script
This script truncates all tables in the database, removing all data while preserving table structures.
Use this when preparing for production to remove test data.
"""

from db_connect_pooled import db_manager

def clear_all_data():
    """Clear all data from all tables in the database"""
    print("="*60)
    print("CLEAR ALL DATA - PRODUCTION RESET")
    print("="*60)
    print("\nThis script will DELETE ALL DATA from:")
    print("  - daily_reports")
    print("  - daily_reports_brand_a")
    print("  - daily_reports_summary")
    print("  - payable_tbl")
    print("  - users (including all client accounts)")
    print("  - branches")
    print("  - corporations")
    print("\nTable structures will be preserved, only data will be removed.")
    print("="*60)
    
    response = input("\nAre you ABSOLUTELY SURE you want to delete all data? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\nOperation cancelled. No data was deleted.")
        return
    
    # Double confirmation for safety
    print("\n⚠️  FINAL WARNING: This cannot be undone!")
    response2 = input("Type 'DELETE ALL DATA' to confirm: ").strip()
    
    if response2 != 'DELETE ALL DATA':
        print("\nOperation cancelled. No data was deleted.")
        return
    
    print("\nStarting data deletion...")
    
    try:
        # Disable foreign key checks to avoid constraint errors
        print("\n1. Disabling foreign key checks...")
        db_manager.execute_query("SET FOREIGN_KEY_CHECKS = 0")
        print("   ✓ Foreign key checks disabled")
        
        # Truncate tables in order (child tables first to avoid FK issues)
        tables = [
            "daily_reports_summary",
            "payable_tbl",
            "daily_reports_brand_a",
            "daily_reports",
            "users",
            "branches",
            "corporations"
        ]
        
        print("\n2. Clearing table data...")
        for table in tables:
            try:
                result = db_manager.execute_query(f"TRUNCATE TABLE {table}")
                print(f"   ✓ Cleared all data from '{table}'")
            except Exception as e:
                print(f"   ⚠️  Could not clear '{table}': {e}")
        
        # Re-enable foreign key checks
        print("\n3. Re-enabling foreign key checks...")
        db_manager.execute_query("SET FOREIGN_KEY_CHECKS = 1")
        print("   ✓ Foreign key checks re-enabled")
        
        print("\n" + "="*60)
        print("✅ ALL DATA SUCCESSFULLY DELETED")
        print("="*60)
        print("\nYour database is now clean and ready for production!")
        print("You can now:")
        print("  1. Create new corporations")
        print("  2. Create new branches")
        print("  3. Create new client accounts")
        print("  4. Start entering production data")
        
    except Exception as e:
        print(f"\n❌ Error during data deletion: {e}")
        # Try to re-enable foreign key checks even on error
        try:
            db_manager.execute_query("SET FOREIGN_KEY_CHECKS = 1")
        except:
            pass
        raise

def clear_specific_table():
    """Clear data from a specific table only"""
    print("="*60)
    print("CLEAR SPECIFIC TABLE")
    print("="*60)
    print("\nAvailable tables:")
    print("  1. daily_reports - All daily report entries (Brand B)")
    print("  2. daily_reports_brand_a - All daily report entries (Brand A)")
    print("  3. daily_reports_summary - Summary data")
    print("  4. payable_tbl - Payable records")
    print("  5. users - All user accounts (clients and admins)")
    print("  6. branches - All branches")
    print("  7. corporations - All corporations")
    print("="*60)
    
    table_name = input("\nEnter table name to clear (or 'cancel'): ").strip().lower()
    
    valid_tables = ["daily_reports", "daily_reports_brand_a", "daily_reports_summary", 
                    "payable_tbl", "users", "branches", "corporations"]
    
    if table_name == 'cancel':
        print("Operation cancelled.")
        return
    
    if table_name not in valid_tables:
        print(f"❌ Invalid table name. Must be one of: {', '.join(valid_tables)}")
        return
    
    print(f"\n⚠️  WARNING: This will delete ALL data from the '{table_name}' table!")
    response = input(f"Type '{table_name}' to confirm deletion: ").strip().lower()
    
    if response != table_name:
        print("Operation cancelled.")
        return
    
    try:
        db_manager.execute_query("SET FOREIGN_KEY_CHECKS = 0")
        result = db_manager.execute_query(f"TRUNCATE TABLE {table_name}")
        db_manager.execute_query("SET FOREIGN_KEY_CHECKS = 1")
        
        print(f"\n✅ Successfully cleared all data from '{table_name}'")
        
    except Exception as e:
        print(f"\n❌ Error clearing table: {e}")
        try:
            db_manager.execute_query("SET FOREIGN_KEY_CHECKS = 1")
        except:
            pass

if __name__ == "__main__":
    import sys
    
    print("\nWhat would you like to do?")
    print("  1. Clear ALL data from ALL tables (production reset)")
    print("  2. Clear data from a specific table only")
    print("  3. Cancel")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice == "1":
        clear_all_data()
    elif choice == "2":
        clear_specific_table()
    else:
        print("Operation cancelled.")
        sys.exit(0)
