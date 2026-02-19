"""
Security Migration Script
- Creates initial admin user in database with hashed password
- Migrates existing plaintext passwords to bcrypt
"""

from db_connect_pooled import db_manager
from security import hash_password, is_password_hashed


def create_admin_user(username: str = "admin", password: str = "Admin1234"):
    """
    Create an admin user in the database with a hashed password.
    This replaces the hardcoded admin credentials.
    """
    print(f"Creating admin user: {username}")
    
    # Check if admin already exists
    existing = db_manager.execute_query(
        "SELECT id, password FROM users WHERE username = %s AND role = 'admin'",
        (username,)
    )
    
    if existing:
        print(f"Admin user '{username}' already exists (ID: {existing[0]['id']})")
        
        # Check if password is hashed
        stored_pw = existing[0].get('password', '')
        if stored_pw and not is_password_hashed(stored_pw):
            print("Password is plaintext - migrating to bcrypt...")
            hashed = hash_password(password)
            db_manager.execute_query(
                "UPDATE users SET password = %s WHERE id = %s",
                (hashed, existing[0]['id'])
            )
            print("✓ Password migrated to bcrypt")
        elif stored_pw and is_password_hashed(stored_pw):
            print("✓ Password is already hashed")
        return existing[0]['id']
    
    # Hash the password
    hashed_password = hash_password(password)
    
    # Insert admin user
    result = db_manager.execute_query(
        """INSERT INTO users (username, password, first_name, last_name, role, corporation, branch)
           VALUES (%s, %s, %s, %s, 'admin', 'Admin', 'Admin')""",
        (username, hashed_password, 'System', 'Administrator')
    )
    
    if result is not None:
        # Get the created user ID
        row = db_manager.execute_query(
            "SELECT id FROM users WHERE username = %s AND role = 'admin'",
            (username,)
        )
        if row:
            print(f"✓ Admin user created successfully!")
            print(f"  Username: {username}")
            print(f"  ID: {row[0]['id']}")
            print(f"  Password: {password} (hashed with bcrypt)")
            return row[0]['id']
    
    print("✗ Failed to create admin user")
    return None


def migrate_all_passwords():
    """
    Migrate all existing plaintext passwords to bcrypt hashes.
    This is a one-time migration for existing users.
    """
    print("\n=== Password Migration ===")
    print("Checking for plaintext passwords...")
    
    # Get all users with passwords
    users = db_manager.execute_query(
        "SELECT id, username, password FROM users WHERE password IS NOT NULL"
    )
    
    if not users:
        print("No users found with passwords")
        return
    
    migrated = 0
    already_hashed = 0
    failed = 0
    
    for user in users:
        user_id = user['id']
        username = user['username']
        password = user.get('password', '')
        
        if not password:
            continue
        
        if is_password_hashed(password):
            already_hashed += 1
            continue
        
        # This is a plaintext password - hash it
        # Note: We cannot know the original password if it was already hashed
        # So we hash what is stored (assuming it's plaintext)
        try:
            hashed = hash_password(password)
            db_manager.execute_query(
                "UPDATE users SET password = %s WHERE id = %s",
                (hashed, user_id)
            )
            migrated += 1
            print(f"  ✓ Migrated: {username}")
        except Exception as e:
            failed += 1
            print(f"  ✗ Failed for {username}: {e}")
    
    print(f"\nMigration complete:")
    print(f"  - Already hashed: {already_hashed}")
    print(f"  - Migrated: {migrated}")
    print(f"  - Failed: {failed}")


def main():
    print("=" * 50)
    print("Security Migration Script")
    print("=" * 50)
    
    # Test database connection
    if not db_manager.test_connection():
        print("✗ Cannot connect to database")
        return
    
    print("✓ Database connected")
    
    # Create admin user
    create_admin_user("admin", "Admin1234")
    
    # Migrate existing passwords
    migrate_all_passwords()
    
    print("\n" + "=" * 50)
    print("Migration complete!")
    print("=" * 50)
    print("\nIMPORTANT:")
    print("1. Change the default admin password immediately")
    print("2. Delete this script after running (contains default credentials)")


if __name__ == "__main__":
    main()
