#!/usr/bin/env python3
"""
Automatic daily migration of palawan details from daily_reports to payable_tbl_brand_a.
Scheduled to run at 8:30 AM every day.

This script:
1. Migrates palawan details from daily_reports (Brand B) to payable_tbl_brand_a
2. Migrates palawan details from daily_reports_brand_a (Brand A) to payable_tbl_brand_a
3. Checks for duplicates to avoid re-migration
4. DELETES successfully migrated records from daily_reports tables
5. Logs all activity to a file with timestamp
"""

from api_db_manager import db_manager
import logging
from datetime import datetime
import os

# Set up logging with timestamp
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f'palawan_migration_{datetime.now().strftime("%Y%m%d")}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_if_exists_in_payable(corporation, branch, date_str):
    """Check if record already exists in payable_tbl_brand_a"""
    try:
        result = db_manager.execute_query("""
            SELECT COUNT(*) as cnt
            FROM payable_tbl_brand_a
            WHERE corporation=%s AND branch=%s AND date=%s
        """, (corporation, branch, date_str))

        return result and result[0]['cnt'] > 0
    except Exception as e:
        logger.error(f"Error checking duplicate: {e}")
        return False


def migrate_from_daily_reports():
    """Migrate palawan data from daily_reports (Brand B) to payable_tbl_brand_a"""
    logger.info("=" * 100)
    logger.info("MIGRATING FROM daily_reports (Brand B)")
    logger.info("=" * 100)

    try:
        # Get all records with palawan data from daily_reports
        records = db_manager.execute_query("""
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
            WHERE (palawan_sendout_principal > 0
               OR palawan_payout_principal > 0
               OR palawan_international_principal > 0
               OR palawan_pay_out_incentives > 0
               OR palawan_suki_discounts > 0
               OR palawan_suki_rebates > 0
               OR palawan_cancel > 0)
            ORDER BY date DESC, corporation, branch
        """)

        if not records:
            logger.info("No palawan data found in daily_reports")
            return 0, 0

        logger.info(f"Found {len(records)} records in daily_reports")

        migrated = 0
        skipped_duplicates = 0
        deleted = 0

        for record in records:
            # Check if already exists in payable_tbl_brand_a
            if check_if_exists_in_payable(record['corporation'], record['branch'], record['date']):
                logger.info(f"  SKIPPED (duplicate): {record['branch']} {record['date']} ({record['corporation']})")
                skipped_duplicates += 1
                continue

            try:
                # Insert into payable_tbl_brand_a
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
                        record['corporation'], record['branch'], record['date'],
                        record['so_lotes'], record['so_principal'], record['so_sc'],
                        record['so_commission'], record['so_total'],
                        record['po_lotes'], record['po_principal'], record['po_sc'],
                        record['po_commission'], record['po_total'],
                        record['int_lotes'], record['int_principal'], record['int_sc'],
                        record['int_commission'], record['int_total'],
                        record['inc'], record['skid'], record['skir'], record['cancellation'],
                    )
                )

                # Delete palawan data from daily_reports after successful migration
                db_manager.execute_query("""
                    UPDATE daily_reports
                    SET palawan_sendout_principal = 0,
                        palawan_sendout_sc = 0,
                        palawan_sendout_commission = 0,
                        palawan_sendout_regular_total = 0,
                        palawan_sendout_lotes_total = 0,
                        palawan_payout_principal = 0,
                        palawan_payout_sc = 0,
                        palawan_payout_commission = 0,
                        palawan_payout_regular_total = 0,
                        palawan_payout_lotes_total = 0,
                        palawan_international_principal = 0,
                        palawan_international_sc = 0,
                        palawan_international_commission = 0,
                        palawan_international_regular_total = 0,
                        palawan_international_lotes_total = 0,
                        palawan_pay_out_incentives = 0,
                        palawan_suki_discounts = 0,
                        palawan_suki_rebates = 0,
                        palawan_cancel = 0
                    WHERE corporation=%s AND branch=%s AND date=%s
                """, (record['corporation'], record['branch'], record['date']))

                migrated += 1
                deleted += 1
                logger.info(f"  MIGRATED & DELETED: {record['branch']} {record['date']} ({record['corporation']})")

            except Exception as e:
                logger.error(f"Failed to migrate {record['branch']} {record['date']}: {e}")

        logger.info(f"\ndaily_reports migration complete:")
        logger.info(f"  - Migrated: {migrated}")
        logger.info(f"  - Deleted from source: {deleted}")
        logger.info(f"  - Skipped (duplicates): {skipped_duplicates}")

        return migrated, skipped_duplicates

    except Exception as e:
        logger.error(f"Error migrating from daily_reports: {e}")
        return 0, 0


def migrate_from_daily_reports_brand_a():
    """Migrate palawan data from daily_reports_brand_a (Brand A) to payable_tbl_brand_a"""
    logger.info("=" * 100)
    logger.info("MIGRATING FROM daily_reports_brand_a (Brand A)")
    logger.info("=" * 100)

    try:
        # Get all records with palawan data from daily_reports_brand_a
        records = db_manager.execute_query("""
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
            FROM daily_reports_brand_a
            WHERE (palawan_sendout_principal > 0
               OR palawan_payout_principal > 0
               OR palawan_international_principal > 0
               OR palawan_pay_out_incentives > 0
               OR palawan_suki_discounts > 0
               OR palawan_suki_rebates > 0
               OR palawan_cancel > 0)
            ORDER BY date DESC, corporation, branch
        """)

        if not records:
            logger.info("No palawan data found in daily_reports_brand_a")
            return 0, 0

        logger.info(f"Found {len(records)} records in daily_reports_brand_a")

        migrated = 0
        skipped_duplicates = 0
        deleted = 0

        for record in records:
            # Check if already exists in payable_tbl_brand_a
            if check_if_exists_in_payable(record['corporation'], record['branch'], record['date']):
                logger.info(f"  SKIPPED (duplicate): {record['branch']} {record['date']} ({record['corporation']})")
                skipped_duplicates += 1
                continue

            try:
                # Insert into payable_tbl_brand_a
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
                        record['corporation'], record['branch'], record['date'],
                        record['so_lotes'], record['so_principal'], record['so_sc'],
                        record['so_commission'], record['so_total'],
                        record['po_lotes'], record['po_principal'], record['po_sc'],
                        record['po_commission'], record['po_total'],
                        record['int_lotes'], record['int_principal'], record['int_sc'],
                        record['int_commission'], record['int_total'],
                        record['inc'], record['skid'], record['skir'], record['cancellation'],
                    )
                )

                # Delete palawan data from daily_reports_brand_a after successful migration
                db_manager.execute_query("""
                    UPDATE daily_reports_brand_a
                    SET palawan_sendout_principal = 0,
                        palawan_sendout_sc = 0,
                        palawan_sendout_commission = 0,
                        palawan_sendout_regular_total = 0,
                        palawan_sendout_lotes_total = 0,
                        palawan_payout_principal = 0,
                        palawan_payout_sc = 0,
                        palawan_payout_commission = 0,
                        palawan_payout_regular_total = 0,
                        palawan_payout_lotes_total = 0,
                        palawan_international_principal = 0,
                        palawan_international_sc = 0,
                        palawan_international_commission = 0,
                        palawan_international_regular_total = 0,
                        palawan_international_lotes_total = 0,
                        palawan_pay_out_incentives = 0,
                        palawan_suki_discounts = 0,
                        palawan_suki_rebates = 0,
                        palawan_cancel = 0
                    WHERE corporation=%s AND branch=%s AND date=%s
                """, (record['corporation'], record['branch'], record['date']))

                migrated += 1
                deleted += 1
                logger.info(f"  MIGRATED & DELETED: {record['branch']} {record['date']} ({record['corporation']})")

            except Exception as e:
                logger.error(f"Failed to migrate {record['branch']} {record['date']}: {e}")

        logger.info(f"\ndaily_reports_brand_a migration complete:")
        logger.info(f"  - Migrated: {migrated}")
        logger.info(f"  - Deleted from source: {deleted}")
        logger.info(f"  - Skipped (duplicates): {skipped_duplicates}")

        return migrated, skipped_duplicates

    except Exception as e:
        logger.error(f"Error migrating from daily_reports_brand_a: {e}")
        return 0, 0


if __name__ == "__main__":
    try:
        logger.info("\n" + "=" * 100)
        logger.info(f"DAILY PALAWAN MIGRATION STARTED at {datetime.now()}")
        logger.info("=" * 100)

        # Step 1: Migrate from daily_reports (Brand B)
        brand_b_migrated, brand_b_skipped = migrate_from_daily_reports()

        # Step 2: Migrate from daily_reports_brand_a (Brand A)
        brand_a_migrated, brand_a_skipped = migrate_from_daily_reports_brand_a()

        # Summary
        logger.info("\n" + "=" * 100)
        logger.info("DAILY MIGRATION SUMMARY")
        logger.info("=" * 100)
        logger.info(f"Brand B (daily_reports):")
        logger.info(f"  - Migrated & Deleted: {brand_b_migrated}")
        logger.info(f"  - Skipped (duplicates): {brand_b_skipped}")
        logger.info(f"\nBrand A (daily_reports_brand_a):")
        logger.info(f"  - Migrated & Deleted: {brand_a_migrated}")
        logger.info(f"  - Skipped (duplicates): {brand_a_skipped}")
        logger.info(f"\nTotal:")
        logger.info(f"  - Migrated & Deleted: {brand_b_migrated + brand_a_migrated}")
        logger.info(f"  - Skipped (duplicates): {brand_b_skipped + brand_a_skipped}")
        logger.info(f"Completed at {datetime.now()}")
        logger.info("=" * 100 + "\n")

    except Exception as e:
        logger.error(f"CRITICAL ERROR: Migration failed: {e}", exc_info=True)
        exit(1)
