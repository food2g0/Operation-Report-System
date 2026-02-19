from db_connect import db_manager

# Check if unique index exists
q = "SELECT COUNT(*) AS cnt FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='daily_reports' AND INDEX_NAME='uq_report_per_day'"
r = db_manager.execute_query(q)
if r and isinstance(r, list) and r[0].get('cnt',0) > 0:
    print('Unique index already exists')
else:
    try:
        alter = "ALTER TABLE daily_reports ADD UNIQUE KEY uq_report_per_day (username, `date`)"
        res = db_manager.execute_query(alter)
        print('Added unique key, result:', res)
    except Exception as e:
        print('Failed to add unique key:', e)
