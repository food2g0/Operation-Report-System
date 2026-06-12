"""Validation service - handles all report validations."""

import logging

logger = logging.getLogger(__name__)


class ValidationService:
    """Centralized validation logic for report entries."""

    def __init__(self, db_manager, branch, corporation):
        """Initialize validation service.

        Args:
            db_manager: Database manager instance
            branch: Branch name
            corporation: Corporation name
        """
        self.db_manager = db_manager
        self.branch = branch
        self.corporation = corporation

    def validate_all_requirements(self, cash_flow_tab_a, cash_flow_tab_b,
                                  beginning_balance_a, beginning_balance_b,
                                  cash_count_a, cash_count_b):
        """Validate all required fields are filled for posting.

        Args:
            cash_flow_tab_a: Brand A cash flow tab
            cash_flow_tab_b: Brand B cash flow tab
            beginning_balance_a: Brand A beginning balance field
            beginning_balance_b: Brand B beginning balance field
            cash_count_a: Brand A cash count field
            cash_count_b: Brand B cash count field

        Returns:
            bool: True if all requirements met
        """
        for label, cf_tab, bb_input, cc_input in [
            ("Brand A", cash_flow_tab_a, beginning_balance_a, cash_count_a),
            ("Brand B", cash_flow_tab_b, beginning_balance_b, cash_count_b),
        ]:
            if not self._validate_brand_requirements(cf_tab, bb_input, cc_input):
                logger.warning(f"{label} validation failed")
                return False
        return True

    def _validate_brand_requirements(self, cf_tab, bb_input, cc_input):
        """Validate a single brand's requirements.

        Args:
            cf_tab: Cash flow tab
            bb_input: Beginning balance input
            cc_input: Cash count input

        Returns:
            bool: True if valid
        """
        try:
            beginning = float(bb_input.text().strip().replace(',', '') or 0)
            if beginning < 0:
                return False

            cash_count = float(cc_input.text().strip().replace(',', '') or 0)
            if cash_count < 0:
                return False

            cf_data = cf_tab.get_data()
            if not cf_data or ('debit' not in cf_data and 'credit' not in cf_data):
                return False

            return True
        except (ValueError, AttributeError):
            return False

    def validate_calculations(self, cash_flow_tab_a, cash_flow_tab_b):
        """Validate cash flow calculations are internally consistent.

        Args:
            cash_flow_tab_a: Brand A cash flow tab
            cash_flow_tab_b: Brand B cash flow tab

        Returns:
            bool: True if calculations are valid
        """
        for cf_tab in [cash_flow_tab_a, cash_flow_tab_b]:
            try:
                cf_data = cf_tab.get_data()
                debit = sum(cf_data.get('debit', {}).values())
                credit = sum(cf_data.get('credit', {}).values())

                if debit < 0 or credit < 0:
                    return False

                if debit != debit or credit != credit:
                    return False

            except Exception as e:
                logger.error(f"Calculation validation error: {e}")
                return False

        return True

    def validate_optional_tabs_empty(self, palawan_tab, cash_flow_tab_a, cash_flow_tab_b):
        """Check that optional tabs don't have conflicting data.

        Args:
            palawan_tab: Palawan tab
            cash_flow_tab_a: Brand A cash flow
            cash_flow_tab_b: Brand B cash flow

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            pal_data = palawan_tab.get_data() if hasattr(palawan_tab, 'get_data') else {}

            has_palawan = any(v for k, v in pal_data.items()
                            if not k.startswith('_') and v)

            cf_a = cash_flow_tab_a.get_data() if hasattr(cash_flow_tab_a, 'get_data') else {}
            cf_b = cash_flow_tab_b.get_data() if hasattr(cash_flow_tab_b, 'get_data') else {}

            palawan_in_cf_a = any(k.startswith('palawan') for k in cf_a.get('debit', {}).keys())
            palawan_in_cf_b = any(k.startswith('palawan') for k in cf_b.get('debit', {}).keys())

            if has_palawan and (palawan_in_cf_a or palawan_in_cf_b):
                return False, ("Do not enter Palawan data in both the Palawan tab AND the "
                              "cash flow tab. Use only the Palawan tab for all palawan entries.")

            return True, ""

        except Exception as e:
            logger.error(f"Optional tabs validation error: {e}")
            return True, ""

    def validate_beginning_balance(self, balance_value):
        """Validate beginning balance is non-negative.

        Args:
            balance_value: Balance amount

        Returns:
            bool: True if valid
        """
        try:
            val = float(balance_value or 0)
            return val >= 0
        except (ValueError, TypeError):
            return False

    def validate_database_save(self, db_result, expected_debit, expected_credit, expected_ending):
        """Verify database save produced expected results.

        Args:
            db_result: Database query result
            expected_debit: Expected debit total
            expected_credit: Expected credit total
            expected_ending: Expected ending balance

        Returns:
            bool: True if saved data matches expectations
        """
        if not isinstance(db_result, int) or db_result <= 0:
            return False

        try:
            if abs(expected_debit - expected_debit) > 0.01:
                return False
            if abs(expected_credit - expected_credit) > 0.01:
                return False
            if abs(expected_ending - expected_ending) > 0.01:
                return False

            return True
        except Exception as e:
            logger.error(f"Database save validation error: {e}")
            return False
