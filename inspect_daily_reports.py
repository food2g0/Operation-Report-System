from db_connect import db_manager
import math

q = "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE, COLUMN_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='daily_reports' ORDER BY ORDINAL_POSITION"
cols = db_manager.execute_query(q)
if not cols:
    print('No columns found or table missing')
    raise SystemExit(1)

fixed_bytes = 0
variable_cols = []
col_count = len(cols)
print(f"Found {col_count} columns in daily_reports\n")

for c in cols:
    name = c['COLUMN_NAME']
    dtype = c['DATA_TYPE']
    char_len = c.get('CHARACTER_MAXIMUM_LENGTH')
    num_prec = c.get('NUMERIC_PRECISION')
    num_scale = c.get('NUMERIC_SCALE')
    col_type = c.get('COLUMN_TYPE')
    is_nullable = c.get('IS_NULLABLE')

    est = None
    note = ''
    if dtype in ('int','integer'):
        est = 4
    elif dtype=='tinyint':
        est = 1
    elif dtype=='smallint':
        est = 2
    elif dtype=='mediumint':
        est = 3
    elif dtype=='bigint':
        est = 8
    elif dtype in ('date',):
        est = 3
    elif dtype in ('datetime','timestamp'):
        est = 8
    elif dtype in ('decimal','numeric'):
        P = int(num_prec) if num_prec else 10
        S = int(num_scale) if num_scale else 0
        int_digits = P - S
        frac_digits = S
        groups_int = int_digits // 9
        groups_frac = frac_digits // 9
        int_left = int_digits % 9
        frac_left = frac_digits % 9
        est = groups_int*4 + groups_frac*4 + ((int_left + 1)//2) + ((frac_left +1)//2)
    elif dtype in ('char',):
        est = int(char_len) if char_len else 0
    elif dtype in ('varchar',):
        # length prefix 1 or 2 bytes
        prefix = 1 if (char_len and char_len<=255) else 2
        est = (int(char_len) if char_len else 0) + prefix
        variable_cols.append((name, col_type))
        note = 'variable'
    elif dtype in ('text','longtext','mediumtext','tinytext','json','blob'):
        variable_cols.append((name, col_type))
        note = 'variable (off-row or large)'
    else:
        # unknown/other -> treat as variable
        variable_cols.append((name, col_type))
        note = 'variable/unknown'

    if est is not None:
        fixed_bytes += est
        print(f"{name:40} {dtype:12} est_bytes={est:3} nullable={is_nullable} {note}")
    else:
        print(f"{name:40} {dtype:12} est_bytes=? nullable={is_nullable} {note}")

print('\nEstimated fixed-width bytes per row (sum of fixed columns):', fixed_bytes)
print('Variable/large columns:')
for v in variable_cols:
    print(' -', v[0], v[1])

MAX_ROW = 65535
print(f"\nMySQL row-size limit (approx): {MAX_ROW} bytes")
if fixed_bytes >= MAX_ROW:
    print('\nWARNING: Estimated fixed-size columns exceed or approach the row-size limit. Consider normalization or storing large/optional fields in separate tables or as JSON/text columns.')
else:
    print('\nFixed-size footprint is within limits, but consider variable columns and TEXT/JSON impact on storage and query performance.')

print('\nRecommendations:')
print('- If many fields are optional/sparse, normalize into child tables (one row per transaction) to avoid wide tables.')
print('- If fields are stable and frequently queried together, wide schema is acceptable.')
print("- Consider storing dynamic or rarely queried groups in a JSON or separate table (easier migrations and smaller row size).")
