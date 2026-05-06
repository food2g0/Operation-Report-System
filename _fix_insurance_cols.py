import pymysql
from secure_config import get_db_config

cfg = get_db_config()
conn = pymysql.connect(**cfg, autocommit=True)
cur = conn.cursor()
tbl = 'daily_transaction_tbl_brand_a'
cur.execute('SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s', (tbl,))
existing = {row[0] for row in cur.fetchall()}

to_add = [
    ('insurance_philam_60', 'DECIMAL(15,2) DEFAULT 0'),
    ('insurance_philam_90', 'DECIMAL(15,2) DEFAULT 0'),
]
for col, defn in to_add:
    if col not in existing:
        sql = f'ALTER TABLE `{tbl}` ADD COLUMN `{col}` {defn}'
        cur.execute(sql)
        print(f'Added {col}')
    else:
        print(f'Already exists: {col}')

conn.close()
print('Done.')
