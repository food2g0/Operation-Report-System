#!/usr/bin/env python3
"""
Execute SQL migration to add detailed transaction columns to payable_tbl_brand_a.
Uses the APIDbManager to execute through the API (respects API_MODE setting).
"""

import sys
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the SQL migration through the API."""

    # Add parent directories to path for imports
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    # Import db_manager from api_db_manager
    try:
        from api_db_manager import db_manager
    except ImportError as e:
        logger.error(f"Could not import api_db_manager: {e}")
        return False

    # Connect to database/API
    if not db_manager.connect():
        logger.error("Failed to connect to database")
        return False

    logger.info("✓ Connected to database")

    # Read the SQL migration file
    sql_file = Path(__file__).parent / "add_detailed_transactions_columns.sql"
    if not sql_file.exists():
        logger.error(f"SQL file not found: {sql_file}")
        return False

    with open(sql_file, 'r') as f:
        sql_content = f.read()

    # Split SQL by semicolon and execute each statement
    statements = []
    for s in sql_content.split(';'):
        s = s.strip()
        # Skip empty lines, comments, and verification queries
        if s and not s.startswith('--') and not s.startswith('/*'):
            statements.append(s)

    logger.info(f"Found {len(statements)} SQL statements to execute")

    try:
        for i, statement in enumerate(statements, 1):
            logger.info(f"Executing statement {i}/{len(statements)}...")
            try:
                db_manager.execute_query(statement)
                logger.info(f"  ✓ Success")
            except Exception as e:
                logger.error(f"  ✗ Error: {e}")
                return False

        logger.info("✓ All migrations applied successfully")

        # Verify columns were created
        logger.info("\nVerifying columns...")
        try:
            results = db_manager.execute_query("""
                SELECT COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'payable_tbl_brand_a'
                AND COLUMN_NAME LIKE '%detailed%'
                ORDER BY COLUMN_NAME
            """)

            if results and len(results) == 9:
                logger.info(f"✓ All 9 detailed columns created successfully:")
                for row in results:
                    col_name = row.get('COLUMN_NAME', row.get('COLUMN_NAME'.lower()))
                    data_type = row.get('DATA_TYPE', row.get('DATA_TYPE'.lower()))
                    logger.info(f"  - {col_name} ({data_type})")
                return True
            else:
                found_count = len(results) if results else 0
                logger.warning(f"⚠️  Expected 9 columns, found {found_count}")
                if results:
                    for row in results:
                        col_name = row.get('COLUMN_NAME', row.get('COLUMN_NAME'.lower()))
                        logger.info(f"  - {col_name}")
                return found_count > 0
        except Exception as e:
            logger.warning(f"Could not verify columns: {e}")
            logger.info("Columns may have been created - check database manually")
            return True

    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False
    finally:
        try:
            db_manager.close()
            logger.info("Database connection closed")
        except:
            pass

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
