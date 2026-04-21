"""
create_field_config_table.py
─────────────────────────────
Creates a table to store field configurations centrally in the database.
This allows super admin field changes to be visible to all clients immediately.

Run once: python create_field_config_table.py
"""

from db_connect_pooled import db_manager

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS field_config (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    config_key      VARCHAR(50) NOT NULL UNIQUE,
    config_value    LONGTEXT NOT NULL,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by      VARCHAR(120),
    
    INDEX idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def create_table():
    """Create the field_config table if it doesn't exist."""
    try:
        result = db_manager.execute_query(TABLE_SQL)
        if result is not None:
            print("✅ field_config table created (or already exists)")
            return True
        else:
            print("❌ Failed to create field_config table")
            return False
    except Exception as e:
        print(f"❌ Error creating field_config table: {e}")
        return False


def migrate_existing_config():
    """Migrate existing field_config.json to database."""
    import json
    import os
    
    config_path = os.path.join(os.path.dirname(__file__), "field_config.json")
    
    if not os.path.exists(config_path):
        print("ℹ️ No existing field_config.json to migrate")
        return True
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        config_json = json.dumps(config, ensure_ascii=False)
        
        # Use INSERT ... ON DUPLICATE KEY UPDATE for upsert
        sql = """
            INSERT INTO field_config (config_key, config_value, updated_by)
            VALUES ('field_definitions', %s, 'migration')
            ON DUPLICATE KEY UPDATE config_value = VALUES(config_value), updated_by = 'migration'
        """
        result = db_manager.execute_query(sql, (config_json,))
        
        if result is not None:
            print("✅ Migrated field_config.json to database")
            return True
        else:
            print("❌ Failed to migrate config to database")
            return False
            
    except Exception as e:
        print(f"❌ Error migrating config: {e}")
        return False


if __name__ == "__main__":
    print("Creating field_config table...")
    if create_table():
        print("\nMigrating existing configuration...")
        migrate_existing_config()
    print("\nDone!")
