#!/usr/bin/env python3
"""
Database Index Setup Script
Creates indexes on tables for optimal performance with large datasets.
Can improve query performance by 50-100x!

Usage:
    python setup_database_indexes.py        - Create all indexes
    python setup_database_indexes.py check  - Check existing indexes
    python setup_database_indexes.py status - Show index status
"""

import os
import sys
import time
from datetime import datetime
import logging

try:
    from api_db_manager import db_manager as api_db
except ImportError:
    api_db = None

try:
    from db_manager import db_manager as direct_db
except ImportError:
    direct_db = None

# Get the database manager
db_manager = api_db or direct_db

if not db_manager:
    print("ERROR: Could not import database manager")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Index definitions
INDEXES = {
    'daily_reports': [
        ('idx_date_branch', ['date', 'branch']),
        ('idx_corporation_date', ['corporation', 'date']),
        ('idx_branch', ['branch']),
        ('idx_status', ['status']),
        ('idx_corporation', ['corporation']),
        ('idx_palawan_sendout', ['palawan_sendout_principal']),
        ('idx_palawan_payout', ['palawan_payout_principal']),
    ],
    'daily_reports_brand_a': [
        ('idx_date_branch', ['date', 'branch']),
        ('idx_corporation_date', ['corporation', 'date']),
        ('idx_branch', ['branch']),
        ('idx_corporation', ['corporation']),
    ],
    'payable_tbl_brand_a': [
        ('idx_date_branch', ['date', 'branch']),
        ('idx_corporation_date', ['corporation', 'date']),
        ('idx_branch', ['branch']),
        ('idx_corporation', ['corporation']),
        ('idx_sendout_capital', ['sendout_capital']),
        ('idx_payout_capital', ['payout_capital']),
        ('idx_international_capital', ['international_capital']),
    ],
}


def check_connection():
    """Verify database connection"""
    try:
        if hasattr(db_manager, 'test_connection'):
            if db_manager.test_connection():
                logger.info("✓ Database connection OK")
                return True

        # Try a simple query
        result = db_manager.execute_query("SELECT 1")
        if result:
            logger.info("✓ Database connection OK")
            return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


def get_existing_indexes():
    """Get all existing indexes"""
    try:
        query = """
            SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME, SEQ_IN_INDEX
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = 'operation_report_system'
            AND TABLE_NAME IN ('daily_reports', 'daily_reports_brand_a', 'payable_tbl_brand_a')
            ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
        """
        result = db_manager.execute_query(query)
        return result if result else []
    except Exception as e:
        logger.error(f"Failed to get existing indexes: {e}")
        return []


def check_index_exists(table_name, index_name):
    """Check if an index already exists"""
    try:
        query = """
            SELECT COUNT(*) as cnt
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = 'operation_report_system'
            AND TABLE_NAME = %s
            AND INDEX_NAME = %s
        """
        result = db_manager.execute_query(query, (table_name, index_name))
        return result and result[0]['cnt'] > 0
    except Exception as e:
        logger.error(f"Error checking index: {e}")
        return False


def create_index(table_name, index_name, columns):
    """Create an index on a table"""
    try:
        column_list = ', '.join(columns)
        query = f"ALTER TABLE {table_name} ADD INDEX {index_name} ({column_list})"

        # Check if already exists
        if check_index_exists(table_name, index_name):
            logger.info(f"  ✓ Index already exists: {table_name}.{index_name}")
            return True

        logger.info(f"  Creating index: {table_name}.{index_name} ({column_list})...")
        start = time.time()

        db_manager.execute_query(query)

        elapsed = time.time() - start
        logger.info(f"  ✓ Index created in {elapsed:.2f}s")
        return True

    except Exception as e:
        # Index might already exist - that's OK
        if 'Duplicate key name' in str(e) or 'already exists' in str(e):
            logger.info(f"  ✓ Index already exists: {table_name}.{index_name}")
            return True

        logger.error(f"  ✗ Failed to create index: {e}")
        return False


def create_all_indexes():
    """Create all recommended indexes"""
    logger.info("\n" + "=" * 100)
    logger.info("DATABASE INDEX CREATION")
    logger.info("=" * 100)

    if not check_connection():
        logger.error("Cannot proceed without database connection")
        return False

    total_created = 0
    total_failed = 0

    for table_name, index_list in INDEXES.items():
        logger.info(f"\nTable: {table_name}")
        for index_name, columns in index_list:
            if create_index(table_name, index_name, columns):
                total_created += 1
            else:
                total_failed += 1

    # Analyze tables
    logger.info("\n" + "=" * 100)
    logger.info("ANALYZING TABLES (updating statistics)")
    logger.info("=" * 100)

    for table_name in INDEXES.keys():
        try:
            logger.info(f"Analyzing: {table_name}...")
            query = f"ANALYZE TABLE {table_name}"
            db_manager.execute_query(query)
            logger.info(f"  ✓ Analysis complete")
        except Exception as e:
            logger.error(f"  ✗ Failed to analyze: {e}")

    # Summary
    logger.info("\n" + "=" * 100)
    logger.info("INDEX CREATION SUMMARY")
    logger.info("=" * 100)
    logger.info(f"Created/Verified: {total_created} indexes")
    logger.info(f"Failed: {total_failed} indexes")
    logger.info("\nExpected query improvements: 50-100x faster")
    logger.info(f"Completed at {datetime.now()}")
    logger.info("=" * 100 + "\n")

    return total_failed == 0


def check_indexes():
    """Display all indexes"""
    logger.info("\n" + "=" * 100)
    logger.info("EXISTING INDEXES")
    logger.info("=" * 100)

    indexes = get_existing_indexes()

    if not indexes:
        logger.info("No indexes found")
        return

    current_table = None
    current_index = None

    for idx in indexes:
        table = idx['TABLE_NAME']
        index_name = idx['INDEX_NAME']
        column = idx['COLUMN_NAME']
        seq = idx['SEQ_IN_INDEX']

        if table != current_table:
            logger.info(f"\n{table}:")
            current_table = table
            current_index = None

        if index_name != current_index:
            logger.info(f"  {index_name}")
            current_index = index_name

        logger.info(f"    {seq}. {column}")


def get_table_status():
    """Show table sizes and statistics"""
    logger.info("\n" + "=" * 100)
    logger.info("TABLE STATUS")
    logger.info("=" * 100)

    try:
        query = """
            SELECT
                TABLE_NAME,
                FORMAT(TABLE_ROWS, 0) as Rows,
                ROUND((DATA_LENGTH / 1024 / 1024), 2) AS Data_MB,
                ROUND((INDEX_LENGTH / 1024 / 1024), 2) AS Index_MB,
                ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) AS Total_MB
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'operation_report_system'
            AND TABLE_NAME IN ('daily_reports', 'daily_reports_brand_a', 'payable_tbl_brand_a')
            ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC
        """
        result = db_manager.execute_query(query)

        if not result:
            logger.info("No table information available")
            return

        logger.info(f"\n{'Table Name':<30} {'Rows':<15} {'Data':<12} {'Index':<12} {'Total':<12}")
        logger.info("-" * 80)

        for row in result:
            logger.info(f"{row['TABLE_NAME']:<30} {row['Rows']:<15} {row['Data_MB']:<12} {row['Index_MB']:<12} {row['Total_MB']:<12}")

    except Exception as e:
        logger.error(f"Failed to get table status: {e}")

    logger.info("")


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'check':
            check_indexes()
        elif command == 'status':
            get_table_status()
            check_indexes()
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python setup_database_indexes.py        - Create all indexes")
            print("  python setup_database_indexes.py check  - Check existing indexes")
            print("  python setup_database_indexes.py status - Show table status and indexes")
            sys.exit(1)
    else:
        # Create indexes
        if create_all_indexes():
            logger.info("✓ All indexes created successfully!")
            sys.exit(0)
        else:
            logger.error("✗ Some indexes failed to create")
            sys.exit(1)


if __name__ == "__main__":
    main()
