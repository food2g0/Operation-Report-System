"""
Migration: add 'pending' to the machines.status ENUM.

Run from the project root:
    python scripts/migrations/add_pending_machine_status.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import mysql.connector
from secure_config import get_db_config

SQL = """
ALTER TABLE machines
    MODIFY COLUMN status ENUM('approved','revoked','pending')
    NOT NULL DEFAULT 'pending';
"""


def run():
    cfg = get_db_config()
    if not cfg:
        print("ERROR: Could not load DB config.")
        sys.exit(1)

    print(f"Connecting to {cfg['host']}:{cfg.get('port', 3306)} / {cfg['database']} ...")
    conn = mysql.connector.connect(
        host=cfg["host"],
        port=int(cfg.get("port", 3306)),
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        connection_timeout=10,
    )
    cursor = conn.cursor()
    cursor.execute(SQL)
    conn.commit()
    cursor.close()
    conn.close()
    print("machines.status ENUM updated to include 'pending'. Default changed to 'pending'. Done.")


if __name__ == "__main__":
    run()
