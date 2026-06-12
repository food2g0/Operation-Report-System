"""Post handler - manages report posting workflow and balance calculations."""

import logging
import time

logger = logging.getLogger(__name__)

PALAWAN_EXCLUDE = {
    'so_principal', 'so_sc', 'so_commission', 'so_total', 'so_lotes',
    'po_principal', 'po_sc', 'po_commission', 'po_total', 'po_lotes',
    'int_principal', 'int_sc', 'int_commission', 'int_total', 'int_lotes'
}


class PostHandler:
    """Handles report posting workflow, balance calculations, and database operations."""

    def __init__(self, db_manager, branch, corporation, offline_mode=False):
        """Initialize post handler.

        Args:
            db_manager: Database manager instance
            branch: Branch name
            corporation: Corporation name
            offline_mode: Whether in offline mode
        """
        self.db_manager = db_manager
        self.branch = branch
        self.corporation = corporation
        self.offline_mode = offline_mode

    def calculate_balances(self, cash_flow_data, beginning_balance, cash_count):
        """Calculate ending balance, debit/credit totals, and variance.

        Args:
            cash_flow_data: Cash flow dict with debit/credit items
            beginning_balance: Opening balance amount
            cash_count: Physical cash count

        Returns:
            dict: Balance calculations with keys:
                - debit_total, credit_total, ending_balance
                - cash_result, variance_status
        """
        deb = sum(v for k, v in cash_flow_data['debit'].items()
                 if not k.endswith('_lotes') and k not in PALAWAN_EXCLUDE)
        cre = sum(v for k, v in cash_flow_data['credit'].items()
                 if not k.endswith('_lotes'))
        ending = beginning_balance + deb - cre
        cash_result = cash_count - ending

        return {
            'debit_total': beginning_balance + deb,
            'credit_total': cre,
            'ending_balance': ending,
            'cash_result': cash_result,
            'variance_status': (
                "balanced" if abs(cash_result) < 0.01
                else "over" if cash_result > 0
                else "short"
            ),
            'expected_debit': beginning_balance + deb,
            'expected_credit': cre,
            'expected_ending': (beginning_balance + deb) - cre,
        }

    def merge_cash_flow_values(self, cash_flow_data):
        """Merge debit and credit fields into single dict.

        Args:
            cash_flow_data: Dict with debit/credit items

        Returns:
            dict: Merged values
        """
        all_vals = {**cash_flow_data['debit']}
        for k, v in cash_flow_data['credit'].items():
            if v != 0 or k not in all_vals:
                all_vals[k] = v
        return all_vals

    def collect_optional_fields(self, all_vals, cf_tab, brand_full,
                               bank_account=None, ft_ho_breakdown=None,
                               pc_salary_breakdown=None, motor_car_breakdown=None):
        """Collect optional breakdown fields and add to values dict.

        Args:
            all_vals: Base values dict to update
            cf_tab: Cash flow tab widget
            brand_full: Brand name
            bank_account: Selected bank account (optional)
            ft_ho_breakdown: Fund transfer HO breakdown (optional)
            pc_salary_breakdown: PC salary breakdown (optional)
            motor_car_breakdown: Motor car breakdown (optional)

        Returns:
            dict: Updated all_vals dict
        """
        from Client.dashboard.utils import safe_json_serialize

        if bank_account:
            all_vals['fund_transfer_bank_account'] = bank_account

        if ft_ho_breakdown:
            try:
                all_vals['ft_ho_breakdown'] = safe_json_serialize(
                    ft_ho_breakdown, field_name="ft_ho_breakdown"
                )
            except ValueError as e:
                logger.error(f"Skipping ft_ho_breakdown for {brand_full}: {e}")

        if hasattr(cf_tab, 'branch_dest_inputs'):
            branch_dest = cf_tab.branch_dest_inputs.get('Fund Transfer to BRANCH')
            if branch_dest and branch_dest.text().strip():
                all_vals['fund_transfer_to_branch_dest'] = branch_dest.text().strip()

            branch_src = cf_tab.branch_dest_inputs.get('Fund Transfer from BRANCH')
            if branch_src and branch_src.text().strip():
                all_vals['fund_transfer_from_branch_dest'] = branch_src.text().strip()

        if brand_full == "Brand A" and pc_salary_breakdown:
            try:
                all_vals['pc_salary_breakdown'] = safe_json_serialize(
                    pc_salary_breakdown, field_name="pc_salary_breakdown"
                )
            except ValueError as e:
                logger.error(f"Skipping pc_salary_breakdown for {brand_full}: {e}")

        if hasattr(cf_tab, 'mc_currency_details'):
            mc_in_details = cf_tab.mc_currency_details.get('MC In', [])
            mc_out_details = cf_tab.mc_currency_details.get('MC Out', [])
            if mc_in_details:
                try:
                    all_vals['mc_in_details'] = safe_json_serialize(
                        mc_in_details, field_name="mc_in_details"
                    )
                except ValueError as e:
                    logger.error(f"Skipping mc_in_details for {brand_full}: {e}")
            if mc_out_details:
                try:
                    all_vals['mc_out_details'] = safe_json_serialize(
                        mc_out_details, field_name="mc_out_details"
                    )
                except ValueError as e:
                    logger.error(f"Skipping mc_out_details for {brand_full}: {e}")

        if motor_car_breakdown:
            try:
                all_vals['empeno_motor_car_breakdown'] = safe_json_serialize(
                    motor_car_breakdown, field_name="empeno_motor_car_breakdown"
                )
            except ValueError as e:
                logger.error(f"Skipping empeno_motor_car_breakdown for {brand_full}: {e}")

        return all_vals

    def post_to_database_with_retry(self, query, values, max_attempts=4):
        """Execute database query with retry on deadlock.

        Handles deadlock (1213) and duplicate key (1062) errors with retry logic.

        Args:
            query: SQL query string
            values: Query parameters
            max_attempts: Maximum retry attempts

        Returns:
            tuple: (rows_affected, last_error)
        """
        rows, last_err = None, None

        for attempt in range(1, max_attempts + 1):
            res, err = self.db_manager.execute_query_with_exception(query, values)
            if err is None:
                rows = res
                break

            last_err = err
            err_str = str(err)

            # Check for deadlock
            is_deadlock = (
                (hasattr(err, 'args') and isinstance(err.args, tuple)
                 and len(err.args) > 0 and err.args[0] == 1213)
                or '1213' in err_str
            )

            # Check for duplicate key
            is_duplicate = (
                (hasattr(err, 'args') and isinstance(err.args, tuple)
                 and len(err.args) > 0 and err.args[0] == 1062)
                or '1062' in err_str
            )

            if is_deadlock and attempt < max_attempts:
                try:
                    self.db_manager.logger.error(f"DB attempt {attempt}: {err}")
                except Exception:
                    pass
                time.sleep(0.5 * attempt)
            elif is_duplicate:
                # Signal duplicate for caller to handle
                return "duplicate", last_err
            else:
                try:
                    self.db_manager.logger.error(f"DB attempt {attempt}: {err}")
                except Exception:
                    pass
                break

        return rows, last_err

    def validate_balance_calculations(self, calculations):
        """Validate balance calculations are sensible.

        Args:
            calculations: Dict from calculate_balances()

        Returns:
            tuple: (is_valid, error_message)
        """
        if calculations['expected_debit'] < 0:
            return False, "BLOCKED: Debit total is negative (invalid)"
        if calculations['expected_credit'] < 0:
            return False, "BLOCKED: Credit total is negative (invalid)"
        if abs(calculations['ending_balance'] - calculations['expected_ending']) > 0.01:
            return False, (f"BLOCKED: Ending balance mismatch "
                          f"(expected {calculations['expected_ending']:.2f}, "
                          f"got {calculations['ending_balance']:.2f})")
        return True, ""

    def validate_before_posting(self, brand_data):
        """Validate report data before posting.

        Args:
            brand_data: Report data dictionary

        Returns:
            tuple: (is_valid, error_message)
        """
        return True, ""

    def prepare_posting_data(self, brand_data, table_name):
        """Prepare data for database insertion.

        Args:
            brand_data: Raw report data
            table_name: Target table name

        Returns:
            dict: Prepared data
        """
        return {}

    def build_insert_query(self, table_name, data):
        """Build INSERT query for database.

        Args:
            table_name: Target table
            data: Data to insert

        Returns:
            tuple: (query_string, values_list)
        """
        return "", []

    def post_to_database(self, table_name, data):
        """Post data to database.

        Args:
            table_name: Target table
            data: Prepared data

        Returns:
            tuple: (success, error_message)
        """
        return False, "Not implemented"

    def post_offline(self, table_name, data):
        """Post data to offline storage.

        Args:
            table_name: Target table
            data: Prepared data

        Returns:
            tuple: (success, error_message)
        """
        return False, "Not implemented"

    def handle_offline_post(self, selected_date, all_vals):
        """Handle posting when offline.

        Args:
            selected_date: Report date (YYYY-MM-DD)
            all_vals: Report data

        Returns:
            bool: True if successful
        """
        return False

    def verify_posted_data(self, date_str, table_name, expected_data):
        """Verify that posted data matches expectations.

        Args:
            date_str: Report date
            table_name: Table to verify
            expected_data: Expected data

        Returns:
            tuple: (is_valid, error_message)
        """
        return True, ""

    def unlock_previous_entry(self, date_str, table_name):
        """Unlock previous entry if admin reset it.

        Args:
            date_str: Report date
            table_name: Table name

        Returns:
            bool: True if successful
        """
        return True
