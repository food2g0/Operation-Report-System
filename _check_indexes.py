from db_connect_pooled import db_manager
for table in ['daily_reports_brand_a', 'daily_reports']:
    result = db_manager.execute_query(f'SHOW INDEX FROM {table}')
    print(f'=== {table} ===')
    for r in (result or []):
        key = r.get('Key_name')
        col = r.get('Column_name')
        uniq = not r.get('Non_unique')
        print(f'  {key}: {col} (unique={uniq})')
