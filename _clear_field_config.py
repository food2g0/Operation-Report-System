from db_connect_pooled import db_manager

db_manager.execute_query("DELETE FROM field_config WHERE config_key = 'field_definitions'")
print("Done - field_config DB row deleted. JSON file will be used now.")
