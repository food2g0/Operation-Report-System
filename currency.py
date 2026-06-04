from api_db_manager import APIDbManager

db_manager = APIDbManager()

# Read and execute the SQL file
with open("sql/create_currencies_table.sql", "r") as f:
    sql_statements = f.read().split(";")
    for statement in sql_statements:
        if statement.strip():
            db_manager.execute_query(statement)

print("✅ Currencies table created successfully!")