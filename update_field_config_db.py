#!/usr/bin/env python3
import json
from db_connect_pooled import db_manager

# Load current config from database
result = db_manager.execute_query('SELECT config_value FROM field_config WHERE config_key = "field_definitions" LIMIT 1')
if result:
    cfg = json.loads(result[0]['config_value'])
    
    # Update "Fund Empeno STO. (RENEW)" to "Empeno STO. (RENEW)" in all brands
    for brand in cfg.keys():
        for section in ['credit', 'debit']:
            if section in cfg[brand]:
                for i, field in enumerate(cfg[brand][section]):
                    if field[0] == "Fund Empeno STO. (RENEW)":
                        # Keep the placeholder and DB column the same, just fix the display name
                        cfg[brand][section][i] = ["Empeno STO. (RENEW)", field[1], field[2]]
                        print(f"Updated {brand} {section} field: {cfg[brand][section][i]}")
    
    # Update the database
    new_cfg_json = json.dumps(cfg)
    update_result = db_manager.execute_query(
        'UPDATE field_config SET config_value = %s WHERE config_key = "field_definitions"',
        (new_cfg_json,)
    )
    print(f"\nDatabase updated successfully!")
    print("The app will load the new field name on next restart.")
else:
    print("ERROR: Could not find field_config in database")
