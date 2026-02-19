from db_connect import db_manager

q = "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='daily_reports' AND COLUMN_NAME LIKE '%_lotes'"
cols = db_manager.execute_query(q)
if not cols:
    print('No lotes columns found')
    raise SystemExit(0)

for c in cols:
    name = c['COLUMN_NAME']
    dtype = c['DATA_TYPE']
    if dtype.lower() != 'smallint':
        alter = f"ALTER TABLE daily_reports MODIFY COLUMN `{name}` SMALLINT UNSIGNED DEFAULT 0"
        print('Altering', name)
        res = db_manager.execute_query(alter)
        print('Result:', res)
    else:
        print('Already SMALLINT:', name)

print('Done')
