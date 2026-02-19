"""
WARNING: This script will CLEAR ALL DATA from all tables.
Table structures will be preserved - only data will be deleted.
This action is IRREVERSIBLE.
"""
import os
from db_connect_pooled import db_manager

def clear_all_data():
    """Clear all data from all tables (TRUNCATE)"""
    
    print("=" * 60)
    print("WARNING: THIS WILL DELETE ALL DATA FROM ALL TABLES!")
    print("=" * 60)
    print("\nData will be cleared from:")
    print("  - daily_reports_summary")
    print("  - payable_tbl")
    print("  - daily_reports_brand_a")
    print("  - daily_reports")
    print("  - users")
    print("  - corporations")
    print("  - branches")
    print("\nTable structures will be PRESERVED.")
    print("=" * 60)
    
    confirm = input("\nType 'DELETE ALL DATA' to confirm: ")
    
    if confirm != "DELETE ALL DATA":
        print("Cancelled. No data was deleted.")
        return
    
    double_confirm = input("\nAre you ABSOLUTELY SURE? Type 'YES' to proceed: ")
    
    if double_confirm != "YES":
        print("Cancelled. No data was deleted.")
        return
    
    print("\nClearing data...")
    
    try:
        # Disable foreign key checks
        db_manager.execute_query("SET FOREIGN_KEY_CHECKS = 0")
        
        # Clear tables in order (considering foreign key constraints)
        tables = [
            "daily_reports_summary",
            "payable_tbl", 
            "daily_reports_brand_a",
            "daily_reports",
            "users",
            "branches",
            "corporations"
        ]
        
        for table in tables:
            try:
                query = f"TRUNCATE TABLE `{table}`"
                db_manager.execute_query(query)
                print(f"✓ Cleared data from: {table}")
            except Exception as e:
                print(f"✗ Failed to clear {table}: {e}")
        
        # Re-enable foreign key checks
        db_manager.execute_query("SET FOREIGN_KEY_CHECKS = 1")
        
        print("\n" + "=" * 60)
        print("ALL DATA HAS BEEN CLEARED!")
        print("=" * 60)
        print("\nTables still exist - only data was removed.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        # Try to re-enable foreign key checks
        try:
            db_manager.execute_query("SET FOREIGN_KEY_CHECKS = 1")
        except:
            pass

if __name__ == "__main__":
    clear_all_data()
