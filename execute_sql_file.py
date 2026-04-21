from db_connect_pooled import db_manager
import re

path = 'db_optimizations.sql'
with open(path, 'r', encoding='utf-8') as f:
    sql = f.read()

# Remove /* ... */ comments
sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.S)
# Remove lines starting with --
sql = '\n'.join([ln for ln in sql.splitlines() if not ln.strip().startswith('--')])

# Split statements by semicolon
parts = [p.strip() for p in sql.split(';') if p.strip()]

for i, stmt in enumerate(parts, 1):
    try:
        print(f'Executing statement {i}/{len(parts)}...')
        res = db_manager.execute_query(stmt)
        print('Result:', res)
    except Exception as e:
        print('Error executing statement', i, e)

print('Done')
