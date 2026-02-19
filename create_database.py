import os
from dotenv import load_dotenv
import pymysql

load_dotenv()

host = os.getenv("MYSQL_HOST", "localhost")
port = int(os.getenv("MYSQL_PORT", 3306))
user = os.getenv("MYSQL_USER", "root")
password = os.getenv("MYSQL_PASSWORD", "")
db_name = os.getenv("MYSQL_DATABASE", "operation_db")

print(f"Connecting to MySQL on {host}:{port} as {user} (no database)")

try:
    conn = pymysql.connect(host=host, port=port, user=user, password=password, connect_timeout=10)
    with conn.cursor() as cur:
        sql = f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
        cur.execute(sql)
        print(f"Database '{db_name}' created or already exists.")
    conn.close()
except Exception as e:
    print(f"Failed to create database '{db_name}': {e}")
    raise
