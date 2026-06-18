"""
Migration: create the `machines` table for machine-fingerprint access control.

Run from the project root:
    python scripts/migrations/create_machines_table.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import mysql.connector
from secure_config import get_db_config

SQL = """
CREATE TABLE IF NOT EXISTS machines (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    machine_id    VARCHAR(64)  NOT NULL UNIQUE,
    hostname      VARCHAR(255) DEFAULT NULL,
    branch        VARCHAR(100) DEFAULT NULL,
    username      VARCHAR(255) DEFAULT NULL,
    mac_address   VARCHAR(17)  DEFAULT NULL,
    cpu_info      VARCHAR(500) DEFAULT NULL,
    status        ENUM('approved','revoked') NOT NULL DEFAULT 'approved',
    registered_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen     TIMESTAMP    NULL DEFAULT NULL,
    revoked_at    TIMESTAMP    NULL DEFAULT NULL,
    revoked_by    VARCHAR(255) DEFAULT NULL,
    notes         TEXT         DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
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
    print("machines table created (or already exists). Done.")


if __name__ == "__main__":
    run()
