"""Test saving config to database"""
from db_connect_pooled import db_manager
import json

# Load current config
result = db_manager.execute_query(
    "SELECT config_value FROM field_config WHERE config_key = 'field_definitions' ORDER BY id DESC LIMIT 1"
)
config = json.loads(result[0]['config_value'])

# Show current Test field status
print("Before removal:")
for section in ['debit', 'credit']:
    for f in config.get('Brand A', {}).get(section, []):
        if 'test' in f[0].lower():
            print(f"  Found {f[0]} in Brand A/{section}")

# Remove Test field from credit section
config['Brand A']['credit'] = [f for f in config['Brand A']['credit'] if 'test' not in f[0].lower()]

print("\nAfter removal in memory:")
for section in ['debit', 'credit']:
    for f in config.get('Brand A', {}).get(section, []):
        if 'test' in f[0].lower():
            print(f"  Found {f[0]} in Brand A/{section}")
    else:
        print(f"  No test field in Brand A/{section}")

# Save back to database
config_json = json.dumps(config, ensure_ascii=False)
sql = """
    INSERT INTO field_config (config_key, config_value, updated_by)
    VALUES ('field_definitions', %s, %s)
    ON DUPLICATE KEY UPDATE config_value = VALUES(config_value), updated_by = VALUES(updated_by)
"""
result = db_manager.execute_query(sql, (config_json, 'test_script'))
print(f"\nSave result: {result}")

# Also update the JSON file
import os
config_path = os.path.join(os.path.dirname(__file__), "field_config.json")
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
print(f"Saved to {config_path}")

# Verify
result2 = db_manager.execute_query(
    "SELECT config_value FROM field_config WHERE config_key = 'field_definitions' ORDER BY id DESC LIMIT 1"
)
config2 = json.loads(result2[0]['config_value'])
print("\nAfter save & re-load from DB:")
found = False
for section in ['debit', 'credit']:
    for f in config2.get('Brand A', {}).get(section, []):
        if 'test' in f[0].lower():
            print(f"  Found {f[0]} in Brand A/{section}")
            found = True
if not found:
    print("  No test field found - successfully removed!")
