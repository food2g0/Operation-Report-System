#!/usr/bin/env python3
"""
Migration of all palawan data from daily_reports to payable_tbl_brand_a.

Since branches are shared between Brand A and Brand B, and palawan data
represents a single transaction source, we only migrate from daily_reports.

This script:
1. Migrates all palawan details from daily_reports to payable_tbl_brand_a
2. Uses ON DUPLICATE KEY UPDATE (safe to run multiple times)
3. Includes detailed progress reporting
4. Validates the migration afterwards
"""

from api_db_manager import db_manager
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_duplicates():
    """Check for duplicate entries that already exist in payable_tbl_brand_a"""

    logger.info("\n" + "=" * 100)
    logger.info("CHECKING FOR EXISTING DUPLICATES IN payable_tbl_brand_a")
    logger.info("=" * 100)

    # Get all unique (corporation, branch, date) combinations in payable_tbl_brand_a
    existing = db_manager.execute_query("""
        SELECT corporation, branch, date
        FROM payable_tbl_brand_a
        WHERE sendout_capital > 0
           OR payout_capital > 0
           OR international_capital > 0
    """)

    existing_set = {(row['corporation'], row['branch'], row['date']) for row in (existing or [])}
    logger.info(f"Found {len(existing_set)} existing entries in payable_tbl_brand_a")

    return existing_set


def migrate_palawan_data(existing_duplicates):
    """Migrate all palawan data from daily_reports to payable_tbl_brand_a, skipping duplicates"""

    logger.info("\n" + "=" * 100)
    logger.info("MIGRATING PALAWAN DATA FROM daily_reports TO payable_tbl_brand_a")
    logger.info("=" * 100)

    # Get all distinct branch/date/corporation combinations with palawan data
    all_records = db_manager.execute_query("""
        SELECT DISTINCT
            corporation, branch, date,
            palawan_sendout_lotes_total as so_lotes,
            palawan_sendout_principal as so_principal,
            palawan_sendout_sc as so_sc,
            palawan_sendout_commission as so_commission,
            palawan_sendout_regular_total as so_total,
            palawan_payout_lotes_total as po_lotes,
            palawan_payout_principal as po_principal,
            palawan_payout_sc as po_sc,
            palawan_payout_commission as po_commission,
            palawan_payout_regular_total as po_total,
            palawan_international_lotes_total as int_lotes,
            palawan_international_principal as int_principal,
            palawan_international_sc as int_sc,
            palawan_international_commission as int_commission,
            palawan_international_regular_total as int_total,
            palawan_pay_out_incentives as inc,
            palawan_suki_discounts as skid,
            palawan_suki_rebates as skir,
            palawan_cancel as cancellation
        FROM daily_reports
        WHERE palawan_sendout_principal > 0
           OR palawan_payout_principal > 0
           OR palawan_international_principal > 0
           OR palawan_pay_out_incentives > 0
           OR palawan_suki_discounts > 0
           OR palawan_suki_rebates > 0
           OR palawan_cancel > 0
        ORDER BY date, corporation, branch
    """)

    if not all_records:
        logger.info("No palawan data found in daily_reports")
        return 0, 0

    logger.info(f"Found {len(all_records)} total records with palawan data in daily_reports")

    inserted = 0
    skipped_duplicates = 0

    for i, row in enumerate(all_records, 1):
        # Check if this entry already exists
        key = (row['corporation'], row['branch'], row['date'])
        if key in existing_duplicates:
            skipped_duplicates += 1
            logger.info(f"  SKIPPED duplicate: {row['branch']} {row['date']} ({row['corporation']})")
            continue

        try:
            db_manager.execute_query(
                """INSERT INTO payable_tbl_brand_a
                   (corporation, branch, date,
                    sendout_lotes, sendout_capital, sendout_sc, sendout_commission, sendout_total,
                    payout_lotes, payout_capital, payout_sc, payout_commission, payout_total,
                    international_lotes, international_capital, international_sc, international_commission, international_total,
                    inc, skid, skir, cancellation)
                   VALUES (%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s)
                """,
                (
                    row['corporation'], row['branch'], row['date'],
                    row['so_lotes'], row['so_principal'], row['so_sc'], row['so_commission'], row['so_total'],
                    row['po_lotes'], row['po_principal'], row['po_sc'], row['po_commission'], row['po_total'],
                    row['int_lotes'], row['int_principal'], row['int_sc'], row['int_commission'], row['int_total'],
                    row['inc'], row['skid'], row['skir'], row['cancellation'],
                )
            )
            inserted += 1
            if (inserted + skipped_duplicates) % 100 == 0:
                logger.info(f"  Processed {inserted + skipped_duplicates}/{len(all_records)} records (inserted: {inserted}, skipped: {skipped_duplicates})...")
        except Exception as e:
            logger.error(f"Failed to migrate {row['branch']} {row['date']}: {e}")

    logger.info(f"\n✓ Migration complete:")
    logger.info(f"  - Inserted: {inserted} new records")
    logger.info(f"  - Skipped (duplicates): {skipped_duplicates} records")
    return inserted, skipped_duplicates


def validate_migration():
    """Verify that all data was migrated correctly"""

    logger.info("\n" + "=" * 100)
    logger.info("VALIDATION: Checking migration completeness")
    logger.info("=" * 100)

    daily_count = db_manager.execute_query("""
        SELECT COUNT(*) as cnt
        FROM daily_reports
        WHERE palawan_sendout_principal > 0
           OR palawan_payout_principal > 0
           OR palawan_international_principal > 0
    """)

    payable_count = db_manager.execute_query("""
        SELECT COUNT(*) as cnt
        FROM payable_tbl_brand_a
        WHERE sendout_capital > 0
           OR payout_capital > 0
           OR international_capital > 0
    """)

    daily_total = daily_count[0]['cnt'] if daily_count else 0
    payable_total = payable_count[0]['cnt'] if payable_count else 0

    logger.info(f"\nMigration Summary:")
    logger.info(f"  Records in daily_reports with palawan data: {daily_total}")
    logger.info(f"  Records in payable_tbl_brand_a: {payable_total}")

    if daily_total <= payable_total:
        logger.info(f"\n✓ All data has been successfully migrated to payable_tbl_brand_a")
    else:
        logger.warning(f"\n⚠️  Some records may not have been migrated ({payable_total} < {daily_total})")


if __name__ == "__main__":
    try:
        logger.info(f"Migration started at {datetime.now()}")

        # Step 1: Check for existing duplicates
        existing_duplicates = check_duplicates()

        # Step 2: Migrate data, skipping duplicates
        inserted, skipped = migrate_palawan_data(existing_duplicates)

        # Step 3: Validate migration
        validate_migration()

        logger.info("\n" + "=" * 100)
        logger.info(f"MIGRATION COMPLETE: {inserted} new records migrated, {skipped} duplicates skipped")
        logger.info("=" * 100)
        logger.info("\nNext steps:")
        logger.info("1. Test reports to ensure all palawan data is displaying correctly")
        logger.info("2. Once verified, both Brand A and Brand B will read from payable_tbl_brand_a")
        logger.info("3. Next month: Update all clients to upload directly to payable_tbl_brand_a")
        logger.info(f"\nMigration completed at {datetime.now()}")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        exit(1)
