#!/usr/bin/env python3
"""
Migration Script: Migrate clients table to users table
This script migrates all client data from the clients table to the users table,
then drops the clients table.
"""

from db_connect_pooled import db_manager

def migrate_clients_to_users():
    print("Starting migration from clients table to users table...")
    
    try:
        # Step 1: Add first_name and last_name columns to users table if they don't exist
        print("Step 1: Adding first_name and last_name columns to users table...")
        
        # Check if columns already exist
        check_columns = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'users' 
            AND COLUMN_NAME IN ('first_name', 'last_name')
        """
        existing_columns = db_manager.execute_query(check_columns)
        existing_column_names = [col['COLUMN_NAME'] for col in existing_columns] if existing_columns else []
        
        # Add first_name if it doesn't exist
        if 'first_name' not in existing_column_names:
            alter_query1 = "ALTER TABLE users ADD COLUMN first_name VARCHAR(255)"
            db_manager.execute_query(alter_query1)
            print("  ✓ Added first_name column")
        else:
            print("  ✓ first_name column already exists")
        
        # Add last_name if it doesn't exist
        if 'last_name' not in existing_column_names:
            alter_query2 = "ALTER TABLE users ADD COLUMN last_name VARCHAR(255)"
            db_manager.execute_query(alter_query2)
            print("  ✓ Added last_name column")
        else:
            print("  ✓ last_name column already exists")
        
        # Step 2: Check if clients table exists
        print("\nStep 2: Checking if clients table exists...")
        check_table = "SHOW TABLES LIKE 'clients'"
        result = db_manager.execute_query(check_table)
        
        if not result:
            print("✓ Clients table does not exist. No migration needed.")
            return
        
        print("✓ Clients table found")
        
        # Step 3: Migrate existing client data
        print("\nStep 3: Migrating client data to users table...")
        migrate_query = """
            INSERT INTO users (username, password, first_name, last_name, corporation, branch, role, created_at)
            SELECT 
                c.username,
                NULL as password,
                c.first_name,
                c.last_name,
                corp.name as corporation,
                b.name as branch,
                'user' as role,
                c.created_at
            FROM clients c
            LEFT JOIN corporations corp ON c.corporation_id = corp.id
            LEFT JOIN branches b ON c.branch_id = b.id
            WHERE NOT EXISTS (
                SELECT 1 FROM users u WHERE u.username = c.username
            )
        """
        db_manager.execute_query(migrate_query)
        
        # Count migrated records
        count_query = "SELECT COUNT(*) as count FROM clients"
        count_result = db_manager.execute_query(count_query)
        client_count = count_result[0]['count'] if count_result else 0
        
        print(f"✓ Migrated {client_count} client records to users table")
        print("  Note: Migrated clients will have NULL passwords and need password reset by admin")
        
        # Step 4: Drop the clients table
        print("\nStep 4: Dropping clients table...")
        drop_query = "DROP TABLE IF EXISTS clients"
        db_manager.execute_query(drop_query)
        print("✓ Clients table dropped successfully")
        
        print("\n" + "="*60)
        print("Migration completed successfully!")
        print("="*60)
        print("\nSummary:")
        print(f"- Added first_name and last_name columns to users table")
        print(f"- Migrated {client_count} clients to users table")
        print(f"- Dropped clients table")
        print("\nIMPORTANT: Migrated clients have NULL passwords.")
        print("Please reset passwords for these users using the admin dashboard.")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("Please check the error and try again.")
        raise

if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("CLIENT TO USERS TABLE MIGRATION")
    print("="*60)
    print("\nThis script will:")
    print("1. Add first_name and last_name columns to users table")
    print("2. Migrate all data from clients table to users table")
    print("3. Drop the clients table")
    print("\nWARNING: This is a destructive operation!")
    print("Make sure you have a backup of your database before proceeding.")
    print("="*60)
    
    response = input("\nDo you want to continue? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        try:
            migrate_clients_to_users()
        except Exception:
            sys.exit(1)
    else:
        print("\nMigration cancelled.")
        sys.exit(0)
