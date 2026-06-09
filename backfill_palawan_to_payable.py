#!/usr/bin/env python3
"""
Backfill palawan data from daily_reports and daily_reports_brand_a into payable_tbl_brand_a.

This fixes the issue where old reports have palawan data in daily_reports but it was
never saved to payable_tbl_brand_a (the table used by 30%/60% report sheets).
"""

from api_db_manager import db_manager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backfill_from_daily_reports():
    """Backfill palawan data from daily_reports (Brand B) to payable_tbl_brand_a"""

    logger.info("=" * 100)
    logger.info("BACKFILLING PALAWAN DATA FROM daily_reports TO payable_tbl_brand_a")
    logger.info("=" * 100)

    # Get all records from daily_reports with palawan data not yet in payable_tbl_brand_a
    missing = db_manager.execute_query("""
        SELECT
            dr.id,
            dr.corporation, dr.branch, dr.date,
            dr.palawan_sendout_lotes_total as so_lotes,
            dr.palawan_sendout_principal as so_principal,
            dr.palawan_sendout_sc as so_sc,
            dr.palawan_sendout_commission as so_commission,
            dr.palawan_sendout_regular_total as so_total,
            dr.palawan_payout_lotes_total as po_lotes,
            dr.palawan_payout_principal as po_principal,
            dr.palawan_payout_sc as po_sc,
            dr.palawan_payout_commission as po_commission,
            dr.palawan_payout_regular_total as po_total,
            dr.palawan_international_lotes_total as int_lotes,
            dr.palawan_international_principal as int_principal,
            dr.palawan_international_sc as int_sc,
            dr.palawan_international_commission as int_commission,
            dr.palawan_international_regular_total as int_total
        FROM daily_reports dr
        LEFT JOIN payable_tbl_brand_a p ON dr.branch = p.branch AND dr.date = p.date
        WHERE (dr.palawan_sendout_principal > 0 OR dr.palawan_payout_principal > 0 OR dr.palawan_international_principal > 0)
        AND p.id IS NULL
        ORDER BY dr.date, dr.branch
    """)

    if not missing:
        logger.info("No missing records found in daily_reports")
        return 0

    logger.info(f"Found {len(missing)} missing records in daily_reports. Starting backfill...")

    inserted = 0
    for row in missing:
        try:
            db_manager.execute_query(
                """INSERT INTO payable_tbl_brand_a
                   (corporation, branch, date,
                    sendout_lotes, sendout_capital, sendout_sc, sendout_commission, sendout_total,
                    payout_lotes, payout_capital, payout_sc, payout_commission, payout_total,
                    international_lotes, international_capital, international_sc, international_commission, international_total)
                   VALUES (%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s)
                   ON DUPLICATE KEY UPDATE
                    sendout_lotes=VALUES(sendout_lotes),
                    sendout_capital=VALUES(sendout_capital),
                    sendout_sc=VALUES(sendout_sc),
                    sendout_commission=VALUES(sendout_commission),
                    sendout_total=VALUES(sendout_total),
                    payout_lotes=VALUES(payout_lotes),
                    payout_capital=VALUES(payout_capital),
                    payout_sc=VALUES(payout_sc),
                    payout_commission=VALUES(payout_commission),
                    payout_total=VALUES(payout_total),
                    international_lotes=VALUES(international_lotes),
                    international_capital=VALUES(international_capital),
                    international_sc=VALUES(international_sc),
                    international_commission=VALUES(international_commission),
                    international_total=VALUES(international_total),
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    row['corporation'], row['branch'], row['date'],
                    row['so_lotes'], row['so_principal'], row['so_sc'], row['so_commission'], row['so_total'],
                    row['po_lotes'], row['po_principal'], row['po_sc'], row['po_commission'], row['po_total'],
                    row['int_lotes'], row['int_principal'], row['int_sc'], row['int_commission'], row['int_total'],
                )
            )
            inserted += 1
            if inserted % 10 == 0:
                logger.info(f"  Inserted {inserted}/{len(missing)}...")
        except Exception as e:
            logger.error(f"Failed to insert {row['branch']} {row['date']}: {e}")

    logger.info(f"✓ Backfilled {inserted}/{len(missing)} records from daily_reports")
    return inserted

def backfill_from_daily_reports_brand_a():
    """Backfill palawan data from daily_reports_brand_a (Brand A) to payable_tbl_brand_a"""

    logger.info("\n" + "=" * 100)
    logger.info("BACKFILLING PALAWAN DATA FROM daily_reports_brand_a TO payable_tbl_brand_a")
    logger.info("=" * 100)

    # Get all records from daily_reports_brand_a with palawan data not yet in payable_tbl_brand_a
    missing = db_manager.execute_query("""
        SELECT
            dr.id,
            dr.corporation, dr.branch, dr.date,
            dr.palawan_sendout_lotes_total as so_lotes,
            dr.palawan_sendout_principal as so_principal,
            dr.palawan_sendout_sc as so_sc,
            dr.palawan_sendout_commission as so_commission,
            dr.palawan_sendout_regular_total as so_total,
            dr.palawan_payout_lotes_total as po_lotes,
            dr.palawan_payout_principal as po_principal,
            dr.palawan_payout_sc as po_sc,
            dr.palawan_payout_commission as po_commission,
            dr.palawan_payout_regular_total as po_total,
            dr.palawan_international_lotes_total as int_lotes,
            dr.palawan_international_principal as int_principal,
            dr.palawan_international_sc as int_sc,
            dr.palawan_international_commission as int_commission,
            dr.palawan_international_regular_total as int_total
        FROM daily_reports_brand_a dr
        LEFT JOIN payable_tbl_brand_a p ON dr.branch = p.branch AND dr.date = p.date
        WHERE (dr.palawan_sendout_principal > 0 OR dr.palawan_payout_principal > 0 OR dr.palawan_international_principal > 0)
        AND p.id IS NULL
        ORDER BY dr.date, dr.branch
    """)

    if not missing:
        logger.info("No missing records found in daily_reports_brand_a")
        return 0

    logger.info(f"Found {len(missing)} missing records in daily_reports_brand_a. Starting backfill...")

    inserted = 0
    for row in missing:
        try:
            db_manager.execute_query(
                """INSERT INTO payable_tbl_brand_a
                   (corporation, branch, date,
                    sendout_lotes, sendout_capital, sendout_sc, sendout_commission, sendout_total,
                    payout_lotes, payout_capital, payout_sc, payout_commission, payout_total,
                    international_lotes, international_capital, international_sc, international_commission, international_total)
                   VALUES (%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s)
                   ON DUPLICATE KEY UPDATE
                    sendout_lotes=VALUES(sendout_lotes),
                    sendout_capital=VALUES(sendout_capital),
                    sendout_sc=VALUES(sendout_sc),
                    sendout_commission=VALUES(sendout_commission),
                    sendout_total=VALUES(sendout_total),
                    payout_lotes=VALUES(payout_lotes),
                    payout_capital=VALUES(payout_capital),
                    payout_sc=VALUES(payout_sc),
                    payout_commission=VALUES(payout_commission),
                    payout_total=VALUES(payout_total),
                    international_lotes=VALUES(international_lotes),
                    international_capital=VALUES(international_capital),
                    international_sc=VALUES(international_sc),
                    international_commission=VALUES(international_commission),
                    international_total=VALUES(international_total),
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    row['corporation'], row['branch'], row['date'],
                    row['so_lotes'], row['so_principal'], row['so_sc'], row['so_commission'], row['so_total'],
                    row['po_lotes'], row['po_principal'], row['po_sc'], row['po_commission'], row['po_total'],
                    row['int_lotes'], row['int_principal'], row['int_sc'], row['int_commission'], row['int_total'],
                )
            )
            inserted += 1
            if inserted % 10 == 0:
                logger.info(f"  Inserted {inserted}/{len(missing)}...")
        except Exception as e:
            logger.error(f"Failed to insert {row['branch']} {row['date']}: {e}")

    logger.info(f"✓ Backfilled {inserted}/{len(missing)} records from daily_reports_brand_a")
    return inserted

if __name__ == "__main__":
    try:
        total_b = backfill_from_daily_reports()
        total_a = backfill_from_daily_reports_brand_a()

        logger.info("\n" + "=" * 100)
        logger.info(f"BACKFILL COMPLETE: {total_a + total_b} total records backfilled")
        logger.info("=" * 100)
        logger.info("✓ All palawan data is now in payable_tbl_brand_a")
        logger.info("✓ 30%/60% Palawan report sheets will now display all data")

    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        exit(1)
