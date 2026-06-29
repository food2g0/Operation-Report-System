"""Palawan manager - handles palawan data, adjustments, and payable table synchronization."""

import logging

logger = logging.getLogger(__name__)


class PalawanManager:
    """Manages palawan data, adjustments, and payable table operations."""

    PALAWAN_COLS = (
        'palawan_sendout_principal', 'palawan_sendout_sc',
        'palawan_sendout_commission', 'palawan_sendout_regular_total',
        'palawan_sendout_lotes_total',
        'palawan_payout_principal', 'palawan_payout_sc',
        'palawan_payout_commission', 'palawan_payout_regular_total',
        'palawan_payout_lotes_total',
        'palawan_international_principal', 'palawan_international_sc',
        'palawan_international_commission', 'palawan_international_regular_total',
        'palawan_international_lotes_total',
    )

    PAYABLE_COL_MAPPING = {
        'palawan_sendout_principal': 'sendout_capital',
        'palawan_sendout_sc': 'sendout_sc',
        'palawan_sendout_commission': 'sendout_commission',
        'palawan_sendout_regular_total': 'sendout_total',
        'palawan_sendout_lotes_total': 'sendout_lotes',
        'palawan_payout_principal': 'payout_capital',
        'palawan_payout_sc': 'payout_sc',
        'palawan_payout_commission': 'payout_commission',
        'palawan_payout_regular_total': 'payout_total',
        'palawan_payout_lotes_total': 'payout_lotes',
        'palawan_international_principal': 'international_capital',
        'palawan_international_sc': 'international_sc',
        'palawan_international_commission': 'international_commission',
        'palawan_international_regular_total': 'international_total',
        'palawan_international_lotes_total': 'international_lotes',
    }

    ADJ_MAPPING = {
        'palawan_suki_discounts': 'skid',
        'palawan_suki_rebates': 'skir',
        'palawan_cancel': 'cancellation',
        'palawan_pay_out_incentives': 'inc',
    }

    def __init__(self, db_manager, branch, corporation):
        """Initialize palawan manager.

        Args:
            db_manager: Database manager instance
            branch: Branch name
            corporation: Corporation name
        """
        self.db_manager = db_manager
        self.branch = branch
        self.corporation = corporation

    def restore_palawan_tab(self, date_str):
        """Restore palawan tab data from payable or daily reports tables.

        Tries payable_tbl_brand_a first (primary source for posted reports),
        then falls back to daily_reports tables.

        Args:
            date_str: Date string (YYYY-MM-DD)

        Returns:
            dict: Palawan data with adjustments
        """
        try:
            params = (date_str, self.branch, self.corporation)
            data = {}

            # Try payable_tbl_brand_a first (primary source for all posted palawan data)
            try:
                logger.info(f"🔵 [restore_palawan_tab] Querying payable_tbl_brand_a with params: {params}")
                payable_result = self.db_manager.execute_query(
                    "SELECT * FROM payable_tbl_brand_a "
                    "WHERE date=%s AND branch=%s AND corporation=%s LIMIT 1", params
                )
                logger.info(f"🔵 [restore_palawan_tab] payable_result: {payable_result}")
                if payable_result:
                    payable_row = payable_result[0]
                    # Map payable columns back to both old AND new format keys for UI compatibility
                    for daily_col, payable_col in self.PAYABLE_COL_MAPPING.items():
                        val = payable_row.get(payable_col) or 0
                        try:
                            val_float = float(val)
                        except (TypeError, ValueError):
                            val_float = 0.0
                        if val_float != 0:
                            data[daily_col] = val  # Old format key for compatibility

                    # Also add new-format keys so UI gets data immediately without fallback
                    # Map: payable sendout_capital → so_principal, etc.
                    sendout_capital = payable_row.get('sendout_capital') or 0
                    sendout_sc = payable_row.get('sendout_sc') or 0
                    sendout_commission = payable_row.get('sendout_commission') or 0
                    sendout_total = payable_row.get('sendout_total') or 0
                    sendout_lotes = payable_row.get('sendout_lotes') or 0

                    payout_capital = payable_row.get('payout_capital') or 0
                    payout_sc = payable_row.get('payout_sc') or 0
                    payout_commission = payable_row.get('payout_commission') or 0
                    payout_total = payable_row.get('payout_total') or 0
                    payout_lotes = payable_row.get('payout_lotes') or 0

                    intl_capital = payable_row.get('international_capital') or 0
                    intl_sc = payable_row.get('international_sc') or 0
                    intl_commission = payable_row.get('international_commission') or 0
                    intl_total = payable_row.get('international_total') or 0
                    intl_lotes = payable_row.get('international_lotes') or 0

                    # Add new format keys
                    if float(sendout_capital or 0) != 0: data['so_principal'] = sendout_capital
                    if float(sendout_sc or 0) != 0: data['so_sc'] = sendout_sc
                    if float(sendout_commission or 0) != 0: data['so_commission'] = sendout_commission
                    if float(sendout_total or 0) != 0: data['so_total'] = sendout_total
                    if int(sendout_lotes or 0) != 0: data['so_lotes'] = int(float(sendout_lotes or 0))

                    if float(payout_capital or 0) != 0: data['po_principal'] = payout_capital
                    if float(payout_sc or 0) != 0: data['po_sc'] = payout_sc
                    if float(payout_commission or 0) != 0: data['po_commission'] = payout_commission
                    if float(payout_total or 0) != 0: data['po_total'] = payout_total
                    if int(payout_lotes or 0) != 0: data['po_lotes'] = int(float(payout_lotes or 0))

                    if float(intl_capital or 0) != 0: data['int_principal'] = intl_capital
                    if float(intl_sc or 0) != 0: data['int_sc'] = intl_sc
                    if float(intl_commission or 0) != 0: data['int_commission'] = intl_commission
                    if float(intl_total or 0) != 0: data['int_total'] = intl_total
                    if int(intl_lotes or 0) != 0: data['int_lotes'] = int(float(intl_lotes or 0))

                    # Both Brand A and Brand B adjustments are now in payable_tbl_brand_a
                    inc = payable_row.get('inc') or 0
                    skid = payable_row.get('skid') or 0
                    skir = payable_row.get('skir') or 0
                    cancellation = payable_row.get('cancellation') or 0

                    logger.info(f"[restore_palawan_tab] Adjustments from payable_tbl_brand_a - "
                               f"inc={inc}, skid={skid}, skir={skir}, cancellation={cancellation}")

                    # CRITICAL: Always add adjustment values from payable_tbl_brand_a, even if 0
                    # These are the authoritative values for Palawan Details B tab
                    if inc or inc == 0: data['palawan_pay_out_incentives'] = float(inc or 0)
                    if skid or skid == 0: data['palawan_suki_discounts'] = float(skid or 0)
                    if skir or skir == 0: data['palawan_suki_rebates'] = float(skir or 0)
                    if cancellation or cancellation == 0: data['palawan_cancel'] = float(cancellation or 0)

                    # Pass through detailed transaction JSON so the transaction dialog
                    # still shows existing transactions after an admin reset
                    for _col in (
                        "sendout_detailed_principal", "sendout_detailed_sc", "sendout_detailed_commission",
                        "payout_detailed_principal", "payout_detailed_sc", "payout_detailed_commission",
                        "international_detailed_principal", "international_detailed_sc", "international_detailed_commission",
                    ):
                        _val = payable_row.get(_col)
                        if _val:
                            data[_col] = _val

                    payable_found = True
                    logger.info(f"🔴 [restore_palawan_tab] RETURNING from payable_tbl_brand_a with {len(data)} fields: "
                               f"adjustments={data.get('palawan_pay_out_incentives')}, "
                               f"{data.get('palawan_suki_discounts')}, "
                               f"{data.get('palawan_suki_rebates')}, "
                               f"{data.get('palawan_cancel')}")
                    return data
                else:
                    logger.debug(f"[restore_palawan_tab] No data in payable_tbl_brand_a for {self.branch} on {date_str}")
                    payable_found = False
            except Exception as e:
                logger.warning(f"[restore_palawan_tab] payable_tbl_brand_a query error: {e}")
                payable_found = False

            # Fallback to daily_reports for older data or direct entries
            # CRITICAL: Only load from daily_reports if payable_tbl_brand_a didn't have data
            if payable_found:
                logger.info(f"[restore_palawan_tab] Skipping daily_reports fallback - data already loaded from payable_tbl_brand_a")
                return data

            try:
                logger.info(f"🟡 [restore_palawan_tab] FALLBACK to daily_reports - loading from daily_reports_brand_a and daily_reports")
                result_a = self.db_manager.execute_query(
                    "SELECT * FROM daily_reports_brand_a "
                    "WHERE date=%s AND branch=%s AND corporation=%s LIMIT 1", params
                )
                result_b = self.db_manager.execute_query(
                    "SELECT * FROM daily_reports "
                    "WHERE date=%s AND branch=%s AND corporation=%s LIMIT 1", params
                )
                logger.info(f"🟡 [restore_palawan_tab] result_a: {result_a}, result_b: {result_b}")

                # Load Brand A data (but never overwrite adjustment columns from payable_tbl_brand_a)
                adjustment_cols = {'palawan_pay_out_incentives', 'palawan_suki_discounts',
                                 'palawan_suki_rebates', 'palawan_cancel'}
                if result_a:
                    data_a = dict(result_a[0])
                    for col in self.PALAWAN_COLS:
                        val = data_a.get(col)
                        if val is not None and float(val or 0) != 0:
                            if col not in data and col not in adjustment_cols:
                                data[col] = val

                # Load Brand B data (but never overwrite adjustment columns from payable_tbl_brand_a)
                if result_b:
                    data_b = result_b[0]
                    for col in self.PALAWAN_COLS:
                        b_val = data_b.get(col) or 0
                        try:
                            b_float = float(b_val)
                        except (TypeError, ValueError):
                            b_float = 0.0
                        if b_float != 0:
                            if col not in data and col not in adjustment_cols:
                                data[col] = b_val

                if data:
                    logger.info(f"[restore_palawan_tab] Found {len(data)} fields in daily_reports for {self.branch} on {date_str}")
            except Exception as e:
                logger.warning(f"[restore_palawan_tab] daily_reports fallback error: {e}")

            return data
        except Exception as e:
            logger.error("[restore_palawan_tab] Unexpected error: %s", e)
            return {}

    def get_palawan_adjustments(self, date_str):
        """Fetch palawan adjustments from payable or daily reports.

        Args:
            date_str: Date string (YYYY-MM-DD)

        Returns:
            dict: Adjustment amounts
        """
        mapped = {}

        # Try payable_tbl_brand_a first
        try:
            payable_result = self.db_manager.execute_query(
                "SELECT skid, skir, cancellation, inc "
                "FROM payable_tbl_brand_a "
                "WHERE date=%s AND branch=%s AND corporation=%s LIMIT 1",
                (date_str, self.branch, self.corporation)
            )
            if payable_result:
                row = payable_result[0]
                for daily_col, payable_col in self.ADJ_MAPPING.items():
                    val = row.get(payable_col) or 0
                    try:
                        val_float = float(val)
                    except (TypeError, ValueError):
                        val_float = 0.0
                    if val_float != 0:
                        mapped[daily_col] = val_float
                if mapped:
                    return mapped
        except Exception as e:
            logger.debug(f"[get_palawan_adjustments] payable query: {e}")

        # Fallback to daily_reports_brand_a
        try:
            result_a = self.db_manager.execute_query(
                "SELECT palawan_suki_discounts, palawan_suki_rebates, "
                "palawan_cancel, palawan_pay_out_incentives "
                "FROM daily_reports_brand_a "
                "WHERE date=%s AND branch=%s AND corporation=%s LIMIT 1",
                (date_str, self.branch, self.corporation)
            )
            if result_a:
                row = dict(result_a[0])
                for col in ("palawan_suki_discounts", "palawan_suki_rebates",
                            "palawan_cancel", "palawan_pay_out_incentives"):
                    val = row.get(col) or 0
                    if float(val) != 0:
                        mapped[col] = val
        except Exception as e:
            logger.debug(f"[get_palawan_adjustments] Brand A fallback: {e}")

        # Fallback to daily_reports
        try:
            result_b = self.db_manager.execute_query(
                "SELECT palawan_suki_discounts, palawan_suki_rebates, "
                "palawan_cancel, palawan_pay_out_incentives "
                "FROM daily_reports "
                "WHERE date=%s AND branch=%s AND corporation=%s LIMIT 1",
                (date_str, self.branch, self.corporation)
            )
            if result_b:
                row = dict(result_b[0])
                for col in ("palawan_suki_discounts", "palawan_suki_rebates",
                            "palawan_cancel", "palawan_pay_out_incentives"):
                    val = row.get(col) or 0
                    if float(val) != 0:
                        mapped[col] = val
        except Exception as e:
            logger.debug(f"[get_palawan_adjustments] Brand B fallback: {e}")

        return mapped

    def restore_palawan_payable(self, date_str):
        """Deprecated: Adjustments now loaded in restore_palawan_tab()."""
        pass

    def get_brand_specific_palawan_adjustments(self, date_str, brand_full):
        """Get palawan adjustments specific to a brand.

        CRITICAL: Checks payable_tbl_brand_a FIRST for both brands
        because both Brand A and Brand B adjustments are saved there during posting.
        Falls back to daily_reports_brand_a or daily_reports if not found.

        Args:
            date_str: Date string (YYYY-MM-DD)
            brand_full: Brand name (Brand A or Brand B)

        Returns:
            dict: Brand-specific adjustments
        """
        adj = {}

        # CRITICAL: Always check payable_tbl_brand_a FIRST for both brands
        # Both Brand A and Brand B adjustments are saved to payable_tbl_brand_a during posting
        try:
            payable_result = self.db_manager.execute_query(
                "SELECT inc, skid, skir, cancellation "
                "FROM payable_tbl_brand_a "
                "WHERE date=%s AND branch=%s AND corporation=%s LIMIT 1",
                (date_str, self.branch, self.corporation)
            )
            if payable_result:
                row = dict(payable_result[0])
                inc = float(row.get('inc', 0) or 0)
                skid = float(row.get('skid', 0) or 0)
                skir = float(row.get('skir', 0) or 0)
                cancellation = float(row.get('cancellation', 0) or 0)

                if any([inc, skid, skir, cancellation]):
                    adj = {
                        'palawan_suki_discounts': skid,
                        'palawan_suki_rebates': skir,
                        'palawan_cancel': cancellation,
                        'palawan_pay_out_incentives': inc,
                    }
                    logger.info(f"[get_brand_specific_palawan_adjustments] {brand_full} found in payable_tbl_brand_a: "
                               f"skid={skid}, skir={skir}, cancel={cancellation}, inc={inc}")
                    return adj
        except Exception as e:
            logger.debug(f"[get_brand_specific_palawan_adjustments] payable_tbl_brand_a query error: {e}")

        # Fallback: Query daily_reports tables if not in payable
        table_name = "daily_reports_brand_a" if brand_full == "Brand A" else "daily_reports"
        try:
            result = self.db_manager.execute_query(
                f"SELECT palawan_suki_discounts, palawan_suki_rebates, "
                f"palawan_cancel, palawan_pay_out_incentives "
                f"FROM {table_name} "
                f"WHERE date=%s AND branch=%s AND corporation=%s LIMIT 1",
                (date_str, self.branch, self.corporation)
            )
            if result:
                row = dict(result[0])
                adj = {
                    'palawan_suki_discounts': float(row.get('palawan_suki_discounts', 0) or 0),
                    'palawan_suki_rebates': float(row.get('palawan_suki_rebates', 0) or 0),
                    'palawan_cancel': float(row.get('palawan_cancel', 0) or 0),
                    'palawan_pay_out_incentives': float(row.get('palawan_pay_out_incentives', 0) or 0),
                }
                if any(adj.values()):
                    logger.info(f"[get_brand_specific_palawan_adjustments] {brand_full} found in {table_name}: "
                               f"skid={adj['palawan_suki_discounts']}, skir={adj['palawan_suki_rebates']}, "
                               f"cancel={adj['palawan_cancel']}, inc={adj['palawan_pay_out_incentives']}")
                return adj
        except Exception as e:
            logger.debug(f"[get_brand_specific_palawan_adjustments] {table_name} fallback error: {e}")

        return adj

    def save_palawan_to_payable(self, date_str, brand_full, palawan_data, brand_adjustments=None):
        """Save palawan data to payable_tbl_brand_a for both Brand A and Brand B.

        Both Brand A and Brand B data (including all adjustments: inc, skid, skir, cancellation)
        are saved to payable_tbl_brand_a. ON DUPLICATE KEY UPDATE ensures new adjustments
        are written on each post.

        Args:
            date_str: Date string
            brand_full: Brand name (Brand A or Brand B)
            palawan_data: Palawan data dict
            brand_adjustments: Brand-specific adjustments (optional)

        Returns:
            bool: True if successful
        """
        try:
            so_lotes = int(palawan_data.get('so_lotes', 0) or 0)
            so_principal = float(palawan_data.get('so_principal', 0) or 0)
            so_sc = float(palawan_data.get('so_sc', 0) or 0)
            so_commission = float(palawan_data.get('so_commission', 0) or 0)
            so_total = float(palawan_data.get('so_total', 0) or 0)

            po_lotes = int(palawan_data.get('po_lotes', 0) or 0)
            po_principal = float(palawan_data.get('po_principal', 0) or 0)
            po_sc = float(palawan_data.get('po_sc', 0) or 0)
            po_commission = float(palawan_data.get('po_commission', 0) or 0)
            po_total = float(palawan_data.get('po_total', 0) or 0)

            int_lotes = int(palawan_data.get('int_lotes', 0) or 0)
            int_principal = float(palawan_data.get('int_principal', 0) or 0)
            int_sc = float(palawan_data.get('int_sc', 0) or 0)
            int_commission = float(palawan_data.get('int_commission', 0) or 0)
            int_total = float(palawan_data.get('int_total', 0) or 0)

            if brand_adjustments is None:
                brand_adjustments = {}
            inc = float(brand_adjustments.get('palawan_pay_out_incentives', 0) or
                       palawan_data.get('palawan_pay_out_incentives', 0) or 0)
            skid = float(brand_adjustments.get('palawan_suki_discounts', 0) or
                        palawan_data.get('palawan_suki_discounts', 0) or 0)
            skir = float(brand_adjustments.get('palawan_suki_rebates', 0) or
                        palawan_data.get('palawan_suki_rebates', 0) or 0)
            cancellation = float(brand_adjustments.get('palawan_cancel', 0) or
                                palawan_data.get('palawan_cancel', 0) or 0)

            has_data = any([so_lotes, so_principal, so_sc, so_commission,
                            po_lotes, po_principal, po_sc, po_commission,
                            int_lotes, int_principal, int_sc, int_commission,
                            inc, skid, skir, cancellation])

            if not has_data:
                # No Palawan transactions or adjustments, but if a record already
                # exists (prior submission), update it to zero out stale values
                # such as SKIR so the edit takes effect in the database.
                try:
                    existing = self.db_manager.execute_query(
                        "SELECT 1 FROM payable_tbl_brand_a WHERE branch=%s AND date=%s AND corporation=%s LIMIT 1",
                        (self.branch, date_str, self.corporation)
                    )
                    if existing:
                        self.db_manager.execute_query(
                            "UPDATE payable_tbl_brand_a "
                            "SET inc=0, skid=0, skir=0, cancellation=0, "
                            "sendout_lotes=0, sendout_capital=0, sendout_sc=0, sendout_commission=0, sendout_total=0, "
                            "payout_lotes=0, payout_capital=0, payout_sc=0, payout_commission=0, payout_total=0, "
                            "international_lotes=0, international_capital=0, international_sc=0, international_commission=0, international_total=0, "
                            "updated_at=CURRENT_TIMESTAMP "
                            "WHERE branch=%s AND date=%s AND corporation=%s",
                            (self.branch, date_str, self.corporation)
                        )
                        logger.info(f"Zeroed payable_tbl_brand_a for {self.branch} on {date_str} (all values cleared by user)")
                except Exception as _upd_err:
                    logger.warning(f"Could not zero payable record: {_upd_err}")
                return False

            logger.info(f"🔵 save_palawan_to_payable ({brand_full}): branch={self.branch}, date={date_str}, "
                       f"SO={so_principal}, PO={po_principal}, INT={int_principal}, "
                       f"Adj: inc={inc}, skid={skid}, skir={skir}, cancel={cancellation}")

            # Get detailed transactions if available and ensure they're strings
            so_detailed_principal = palawan_data.get('sendout_detailed_principal')
            so_detailed_sc = palawan_data.get('sendout_detailed_sc')
            so_detailed_commission = palawan_data.get('sendout_detailed_commission')
            po_detailed_principal = palawan_data.get('payout_detailed_principal')
            po_detailed_sc = palawan_data.get('payout_detailed_sc')
            po_detailed_commission = palawan_data.get('payout_detailed_commission')
            int_detailed_principal = palawan_data.get('international_detailed_principal')
            int_detailed_sc = palawan_data.get('international_detailed_sc')
            int_detailed_commission = palawan_data.get('international_detailed_commission')

            logger.info(f"🔵 PalawanManager - Detailed transactions received:")
            logger.info(f"  SO Principal: {so_detailed_principal[:100] if so_detailed_principal else 'None'}...")
            logger.info(f"  SO SC: {so_detailed_sc[:100] if so_detailed_sc else 'None'}...")
            logger.info(f"  SO Commission: {so_detailed_commission[:100] if so_detailed_commission else 'None'}...")
            logger.info(f"  PO Principal: {po_detailed_principal[:100] if po_detailed_principal else 'None'}...")
            logger.info(f"  PO SC: {po_detailed_sc[:100] if po_detailed_sc else 'None'}...")
            logger.info(f"  PO Commission: {po_detailed_commission[:100] if po_detailed_commission else 'None'}...")
            logger.info(f"  INT Principal: {int_detailed_principal[:100] if int_detailed_principal else 'None'}...")
            logger.info(f"  INT SC: {int_detailed_sc[:100] if int_detailed_sc else 'None'}...")
            logger.info(f"  INT Commission: {int_detailed_commission[:100] if int_detailed_commission else 'None'}...")

            sql = """INSERT INTO payable_tbl_brand_a
                   (corporation, branch, date,
                    sendout_lotes, sendout_capital, sendout_sc, sendout_commission, sendout_total,
                    payout_lotes, payout_capital, payout_sc, payout_commission, payout_total,
                    international_lotes, international_capital, international_sc, international_commission, international_total,
                    sendout_detailed_principal, sendout_detailed_sc, sendout_detailed_commission,
                    payout_detailed_principal, payout_detailed_sc, payout_detailed_commission,
                    international_detailed_principal, international_detailed_sc, international_detailed_commission,
                    inc, skid, skir, cancellation)
                   VALUES (%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s,%s)
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
                    sendout_detailed_principal=VALUES(sendout_detailed_principal),
                    sendout_detailed_sc=VALUES(sendout_detailed_sc),
                    sendout_detailed_commission=VALUES(sendout_detailed_commission),
                    payout_detailed_principal=VALUES(payout_detailed_principal),
                    payout_detailed_sc=VALUES(payout_detailed_sc),
                    payout_detailed_commission=VALUES(payout_detailed_commission),
                    international_detailed_principal=VALUES(international_detailed_principal),
                    international_detailed_sc=VALUES(international_detailed_sc),
                    international_detailed_commission=VALUES(international_detailed_commission),
                    inc=VALUES(inc),
                    skid=VALUES(skid),
                    skir=VALUES(skir),
                    cancellation=VALUES(cancellation),
                    updated_at=CURRENT_TIMESTAMP
                """
            params = (
                self.corporation, self.branch, date_str,
                so_lotes, so_principal, so_sc, so_commission, so_total,
                po_lotes, po_principal, po_sc, po_commission, po_total,
                int_lotes, int_principal, int_sc, int_commission, int_total,
                so_detailed_principal, so_detailed_sc, so_detailed_commission,
                po_detailed_principal, po_detailed_sc, po_detailed_commission,
                int_detailed_principal, int_detailed_sc, int_detailed_commission,
                inc, skid, skir, cancellation,
            )

            logger.info(f"🔴 SQL INSERT about to execute with {len(params)} params")
            logger.info(f"  SQL statement: {sql[:200]}...")

            # Log all detailed transaction columns for debugging
            logger.info(f"  Detailed transaction columns:")
            logger.info(f"    sendout_detailed_principal type: {type(so_detailed_principal)}, len: {len(so_detailed_principal) if so_detailed_principal else 0}")
            logger.info(f"    sendout_detailed_principal: {so_detailed_principal[:100] if so_detailed_principal else 'NULL'}...")
            logger.info(f"    sendout_detailed_sc: {so_detailed_sc[:100] if so_detailed_sc else 'NULL'}...")
            logger.info(f"    sendout_detailed_commission: {so_detailed_commission[:100] if so_detailed_commission else 'NULL'}...")
            logger.info(f"    payout_detailed_principal: {po_detailed_principal[:100] if po_detailed_principal else 'NULL'}...")
            logger.info(f"    payout_detailed_sc: {po_detailed_sc[:100] if po_detailed_sc else 'NULL'}...")
            logger.info(f"    payout_detailed_commission: {po_detailed_commission[:100] if po_detailed_commission else 'NULL'}...")
            logger.info(f"    international_detailed_principal: {int_detailed_principal[:100] if int_detailed_principal else 'NULL'}...")
            logger.info(f"    international_detailed_sc: {int_detailed_sc[:100] if int_detailed_sc else 'NULL'}...")
            logger.info(f"    international_detailed_commission: {int_detailed_commission[:100] if int_detailed_commission else 'NULL'}...")

            result, error = self.db_manager.execute_query_with_exception(sql, params)
            logger.info(f"🔴 INSERT result: {result}, error: {error}")

            if error:
                logger.error(f"❌ INSERT FAILED: {error}")
                return False

            if result is None or result == 0:
                logger.warning(f"⚠️ INSERT returned {result} (may indicate 0 rows affected or duplicate key with no changes)")

            # Verify the insert actually worked by querying it back immediately
            verify_params = (date_str, self.branch, self.corporation)
            verify_result = self.db_manager.execute_query(
                "SELECT sendout_detailed_principal FROM payable_tbl_brand_a "
                "WHERE date=%s AND branch=%s AND corporation=%s LIMIT 1",
                verify_params
            )
            if verify_result and verify_result[0].get('sendout_detailed_principal'):
                logger.info(f"✅ Verified: detailed_principal in DB: {verify_result[0]['sendout_detailed_principal'][:100]}...")
            else:
                logger.warning(f"⚠️ Verification query returned: {verify_result} (detailed columns may not be persisting)")

            logger.info(f"Saved {brand_full} palawan data to payable_tbl_brand_a for {self.branch} on {date_str} - "
                       f"inc={inc}, skid={skid}, skir={skir}, cancel={cancellation}")
            return True

        except Exception as e:
            logger.error(f"❌ Could not save palawan data: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def collect_palawan_for_draft(self, palawan_tab):
        """Collect palawan data for draft saving.

        Args:
            palawan_tab: The PalawanTab widget instance

        Returns:
            dict: Palawan data ready for draft
        """
        draft_data = {}
        for section in ("sendout", "payout", "international", "adjustments"):
            for k, w in getattr(palawan_tab, f"{section}_inputs", {}).items():
                draft_data[f"{section}:{k}"] = w.text()
        for k, w in getattr(palawan_tab, "lotes_inputs", {}).items():
            draft_data[f"lotes:{k}"] = w.text()
        # Persist the per-transaction detail entries from the dialog so they
        # survive app close/reopen (stored under a special "transactions" prefix).
        for detail_key, txns in getattr(palawan_tab, "_detailed_transactions", {}).items():
            draft_data[f"transactions:{detail_key}"] = txns
        return draft_data

    def connect_palawan_adjustments_to_brand_b(self, palawan_tab, cash_flow_tab_b, recalc_callback):
        """Connect palawan tab fields to Brand B cash flow fields with auto-sync.

        Args:
            palawan_tab: PalawanTab widget instance
            cash_flow_tab_b: CashFlowTab for Brand B
            recalc_callback: Callback function to recalculate after field change

        Returns:
            int: Number of connections made
        """
        try:
            brand_b_debits = getattr(cash_flow_tab_b, 'debit_inputs', {})
            brand_b_credits = getattr(cash_flow_tab_b, 'credit_inputs', {})

            def make_carry_fn(target_field):
                def carry(text):
                    target_field.blockSignals(True)
                    target_field.setText(text)
                    target_field.blockSignals(False)
                    recalc_callback()
                return carry

            def setup_readonly_field(field):
                field.setReadOnly(True)
                field.setStyleSheet(
                    field.styleSheet() +
                    "background-color: #FEF3C7; color: #92400E;"
                )
                field.setPlaceholderText("Auto from Palawan Details")

            connected_count = 0
            sendout_inputs = getattr(palawan_tab, 'sendout_inputs', {})

            if "Principal" in sendout_inputs and "Palawan Send Out" in brand_b_debits:
                palawan_field = sendout_inputs["Principal"]
                cashflow_field = brand_b_debits["Palawan Send Out"]
                setup_readonly_field(cashflow_field)
                palawan_field.textChanged.connect(make_carry_fn(cashflow_field))
                connected_count += 1

            if "SC" in sendout_inputs and "Commission" in sendout_inputs and "Palawan S.C" in brand_b_debits:
                sc_field = sendout_inputs["SC"]
                commission_field = sendout_inputs["Commission"]
                cashflow_field = brand_b_debits["Palawan S.C"]
                setup_readonly_field(cashflow_field)

                def make_sc_commission_sum_fn(sc_fld, comm_fld, target_fld):
                    def update_sc_commission():
                        try:
                            sc_val = float(sc_fld.text().strip() or 0)
                        except ValueError:
                            sc_val = 0.0
                        try:
                            comm_val = float(comm_fld.text().strip() or 0)
                        except ValueError:
                            comm_val = 0.0

                        total = sc_val + comm_val
                        target_fld.blockSignals(True)
                        target_fld.setText(f"{total:.2f}")
                        target_fld.blockSignals(False)
                        recalc_callback()
                    return update_sc_commission

                update_fn = make_sc_commission_sum_fn(sc_field, commission_field, cashflow_field)
                sc_field.textChanged.connect(update_fn)
                commission_field.textChanged.connect(update_fn)
                connected_count += 1

            payout_inputs = getattr(palawan_tab, 'payout_inputs', {})

            if "Principal" in payout_inputs and "Palawan Pay Out" in brand_b_credits:
                palawan_field = payout_inputs["Principal"]
                cashflow_field = brand_b_credits["Palawan Pay Out"]
                setup_readonly_field(cashflow_field)
                palawan_field.textChanged.connect(make_carry_fn(cashflow_field))
                connected_count += 1

            adjustment_to_cashflow_map = {
                "Palawan Pay Out Incentives": "Palawan Pay Out (incentives)",
                "Palawan Suki Discounts": "Palawan Suki Discounts",
                "Palawan Suki Rebates": "Palawan Suki Rebates",
                "Palawan Cancel": "Palawan Cancel",
            }

            palawan_adjustments = getattr(palawan_tab, 'adjustments_inputs', {})

            for adj_label, cf_label in adjustment_to_cashflow_map.items():
                if adj_label in palawan_adjustments and cf_label in brand_b_credits:
                    palawan_field = palawan_adjustments[adj_label]
                    cashflow_field = brand_b_credits[cf_label]
                    setup_readonly_field(cashflow_field)
                    palawan_field.textChanged.connect(make_carry_fn(cashflow_field))
                    connected_count += 1

            logger.debug("Connected %d Palawan fields to Brand B Cash Flow", connected_count)
            return connected_count

        except Exception as e:
            logger.warning("connect_palawan_adjustments_to_brand_b error (non-fatal): %s", e)
            return 0

    def sync_palawan_between_brands(self, date_str, palawan_data):
        """Synchronize palawan data between brands."""
        pass

    def validate_palawan_data(self, palawan_data):
        """Validate palawan data integrity."""
        return True
