#!/usr/bin/env python3
"""
Migration to add detailed transaction columns to payable_tbl_brand_a.

Adds 9 new JSON columns for storing detailed Palawan transactions:
- sendout_detailed_principal
- sendout_detailed_sc
- sendout_detailed_commission
- payout_detailed_principal
- payout_detailed_sc
- payout_detailed_commission
- international_detailed_principal
- international_detailed_sc
- international_detailed_commission

Each column stores a JSON array of transaction objects:
[{"code": str, "name": str, "amount": float}, ...]
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api_db_manager import APIDbManager
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize DB manager
try:
    from api_config import API_URL, API_KEY
    db_manager = APIDbManager(API_URL, API_KEY)
except ImportError:
    db_manager = APIDbManager()

def check_columns_exist():
    """Check if the new columns already exist in payable_tbl_brand_a."""
    logger.info("\n" + "=" * 100)
    logger.info("CHECKING IF DETAILED TRANSACTION COLUMNS EXIST")
    logger.info("=" * 100)

    try:
        result = db_manager.execute_query("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'payable_tbl_brand_a'
            AND COLUMN_NAME LIKE '%detailed%'
        """)

        if result and len(result) > 0:
            logger.info(f"Found {len(result)} existing detailed columns:")
            for row in result:
                logger.info(f"  - {row['COLUMN_NAME']}")
            return True
        else:
            logger.info("No detailed columns found - ready to add them")
            return False
    except Exception as e:
        logger.error(f"Error checking columns: {e}")
        return False


def add_detailed_columns():
    """Add the detailed transaction columns to payable_tbl_brand_a."""

    logger.info("\n" + "=" * 100)
    logger.info("ADDING DETAILED TRANSACTION COLUMNS")
    logger.info("=" * 100)

    columns_to_add = [
        ("sendout_detailed_principal", "Send-Out Principal"),
        ("sendout_detailed_sc", "Send-Out SC"),
        ("sendout_detailed_commission", "Send-Out Commission"),
        ("payout_detailed_principal", "Pay-Out Principal"),
        ("payout_detailed_sc", "Pay-Out SC"),
        ("payout_detailed_commission", "Pay-Out Commission"),
        ("international_detailed_principal", "International Principal"),
        ("international_detailed_sc", "International SC"),
        ("international_detailed_commission", "International Commission"),
    ]

    for col_name, col_label in columns_to_add:
        try:
            logger.info(f"\n  Adding column: {col_name} ({col_label})")
            db_manager.execute_query(f"""
                ALTER TABLE payable_tbl_brand_a
                ADD COLUMN IF NOT EXISTS {col_name} LONGTEXT COMMENT '{col_label} - JSON array of transactions'
            """)
            logger.info(f"    ✓ Added {col_name}")
        except Exception as e:
            logger.error(f"    ✗ Failed to add {col_name}: {e}")
            return False

    logger.info("\n✓ All detailed transaction columns added successfully")
    return True


def verify_migration():
    """Verify that all new columns were created."""

    logger.info("\n" + "=" * 100)
    logger.info("VERIFYING MIGRATION")
    logger.info("=" * 100)

    try:
        result = db_manager.execute_query("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'payable_tbl_brand_a'
            AND COLUMN_NAME LIKE '%detailed%'
            ORDER BY COLUMN_NAME
        """)

        if result and len(result) == 9:
            logger.info(f"✓ All 9 detailed columns are present:")
            for row in result:
                logger.info(f"  - {row['COLUMN_NAME']}")
            return True
        else:
            found_count = len(result) if result else 0
            logger.warning(f"⚠️  Expected 9 columns, found {found_count}")
            return False
    except Exception as e:
        logger.error(f"Error verifying migration: {e}")
        return False


if __name__ == "__main__":
    try:
        logger.info(f"Migration started at {datetime.now()}")

        # Connect to database
        if not db_manager.connect():
            logger.error("Failed to connect to database")
            exit(1)

        # Step 1: Check if columns already exist
        if check_columns_exist():
            logger.info("\n✓ Detailed transaction columns already exist - no action needed")
            exit(0)

        # Step 2: Add the columns
        if not add_detailed_columns():
            logger.error("\n✗ Failed to add columns")
            exit(1)

        # Step 3: Verify the migration
        if verify_migration():
            logger.info("\n" + "=" * 100)
            logger.info("✓ MIGRATION SUCCESSFUL")
            logger.info("=" * 100)
            logger.info(f"Migration completed at {datetime.now()}")
        else:
            logger.warning("\n⚠️  Migration completed but verification failed")
            exit(1)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        exit(1)
    finally:
        try:
            db_manager.close()
        except:
            pass
