"""Balance manager - handles balance calculations and entry management."""

import datetime
import logging

try:
    from offline_manager import offline_manager, OFFLINE_SUPPORT
except ImportError:
    OFFLINE_SUPPORT = False
    offline_manager = None

logger = logging.getLogger(__name__)


def validate_balance_date_continuity(current_date, returned_date, max_gap_days=None):
    """Validate that balance date is within acceptable gap.

    Args:
        current_date: datetime object for current date
        returned_date: datetime object for returned balance date
        max_gap_days: maximum allowed gap in days (default 10)

    Returns:
        bool: True if gap is acceptable, False otherwise
    """
    if max_gap_days is None:
        max_gap_days = 10

    gap = (current_date - returned_date).days
    return gap <= max_gap_days


def safe_float_cast(value, field_name="", min_val=None, max_val=None):
    """Safely cast value to float with validation.

    Args:
        value: Value to convert
        field_name: Field name for logging
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        float or None: Converted value or None if invalid
    """
    try:
        val = float(value or 0)
        if min_val is not None and val < min_val:
            return None
        if max_val is not None and val > max_val:
            return None
        return val
    except (ValueError, TypeError):
        return None


def validate_table_name(table_name):
    """Validate table name to prevent SQL injection."""
    allowed = {"daily_reports", "daily_reports_brand_a"}
    if table_name not in allowed:
        raise ValueError(f"Invalid table name: {table_name}")
    return table_name


class BalanceManager:
    """Manages balance calculations, validations, and entry locking."""

    def __init__(self, db_manager, branch, corporation, offline_mode=False, user_email=None):
        """Initialize balance manager.

        Args:
            db_manager: Database manager instance
            branch: Branch name
            corporation: Corporation name
            offline_mode: Whether in offline mode
            user_email: User email for offline operations
        """
        self.db_manager = db_manager
        self.branch = branch
        self.corporation = corporation
        self.offline_mode = offline_mode
        self.user_email = user_email

    def get_previous_day_ending_balance(self, selected_date, brand="Brand A"):
        """Get the ending balance from previous day.

        Args:
            selected_date: Date string (YYYY-MM-DD)
            brand: Brand name (Brand A or Brand B)

        Returns:
            tuple: (balance_amount, date_string) or (None, None) if not found
        """
        if self.offline_mode and OFFLINE_SUPPORT and offline_manager:
            return self._get_offline_previous_balance(selected_date, brand)

        try:
            current = datetime.datetime.strptime(selected_date, "%Y-%m-%d")
            table_name = "daily_reports_brand_a" if brand == "Brand A" else "daily_reports"
            table_name = validate_table_name(table_name)

            for days_back in range(1, 11):
                prev_str = (current - datetime.timedelta(days=days_back)).strftime("%Y-%m-%d")
                try:
                    q = f"""SELECT ending_balance FROM {table_name}
                            WHERE date=%s AND branch=%s AND corporation=%s
                            ORDER BY id DESC LIMIT 1"""
                    result = self.db_manager.execute_query(
                        q, (prev_str, self.branch, self.corporation))

                    if result and len(result) > 0:
                        val = result[0].get('ending_balance')
                        if val is not None:
                            safe_val = safe_float_cast(val, field_name="ending_balance", min_val=0)
                            if safe_val is not None:
                                prev_date = datetime.datetime.strptime(prev_str, "%Y-%m-%d")
                                if validate_balance_date_continuity(current, prev_date):
                                    return safe_val, prev_str
                                else:
                                    gap_days = (current - prev_date).days
                                    logger.error(f"Large gap detected ({gap_days} days): Rejecting balance from {prev_str}")
                                    continue
                except Exception as e:
                    logger.warning("Query error for %s: %s", prev_str, e)
        except Exception as e:
            logger.error("get_previous_day_ending_balance(%s): %s", brand, e)
        return None, None

    def _get_offline_previous_balance(self, selected_date, brand):
        """Get previous balance from offline cache.

        Args:
            selected_date: Date string (YYYY-MM-DD)
            brand: Brand name

        Returns:
            tuple: (balance_amount, date_string) or (None, None)
        """
        try:
            pending_bal, pending_date = offline_manager.get_latest_pending_balance(
                self.user_email, self.branch, self.corporation, brand, selected_date
            )

            cached_bal, cached_date = offline_manager.get_cached_balance(
                self.user_email, self.branch, self.corporation, brand
            )

            best_bal, best_date = None, None

            if pending_date and pending_date < selected_date:
                best_bal, best_date = pending_bal, pending_date

            if cached_date and cached_date < selected_date:
                if best_date is None or cached_date > best_date:
                    best_bal, best_date = cached_bal, cached_date

            if pending_date and best_date:
                if pending_date > best_date:
                    best_bal, best_date = pending_bal, pending_date

            return best_bal, best_date

        except Exception as e:
            logger.error("_get_offline_previous_balance error: %s", e)
            return None, None

    def validate_beginning_balance(self, beginning_balance):
        """Validate beginning balance is positive.

        Args:
            beginning_balance: Balance amount

        Returns:
            bool: True if valid
        """
        try:
            val = float(beginning_balance or 0)
            return val >= 0
        except (ValueError, TypeError):
            return False

    def auto_fill_beginning_balance(self, selected_date, brand):
        """Auto-fill beginning balance from previous day.

        Args:
            selected_date: Date string (YYYY-MM-DD)
            brand: Brand identifier (A or B)

        Returns:
            float or None: Auto-filled balance amount
        """
        brand_full = "Brand A" if brand == "A" else "Brand B"
        prev_bal, prev_date = self.get_previous_day_ending_balance(selected_date, brand_full)
        return prev_bal

    def _propagate_opening_balance_to_following_days(self, selected_date, brand_full, ending_balance):
        """Propagate ending balance as opening balance for following days.

        Args:
            selected_date: Current date (YYYY-MM-DD)
            brand_full: Brand name
            ending_balance: Ending balance amount to propagate
        """
        # Placeholder - implement caching logic as needed
        pass
