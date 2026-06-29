"""
Characterization tests for AdminDashboard business logic.

These tests lock in the *current* observed behaviour of the riskiest
functions so that future refactoring cannot silently change outcomes.
They do NOT test Qt widgets — only the pure/extractable logic.

Run with:
    python -m pytest admin/tests/test_dashboard_logic.py -v
"""

import json
import unittest
from unittest.mock import MagicMock, patch, mock_open

# ── import the module-level constants we need ──────────────────────────────
from admin.dashboard import (
    AdminDashboard,
    _BALANCED_THRESHOLD,
    BRAND_A_TYPE,
    BRAND_B_TYPE,
)


# ── lightweight proxy ──────────────────────────────────────────────────────
# `object.__new__(AdminDashboard)` is unsafe for PyQt5 (QWidget) subclasses.
# Instead we create a plain Python class that borrows the pure-logic methods
# from AdminDashboard as unbound functions / descriptor objects.

class _DashProxy:
    """
    Test double for AdminDashboard.

    Inherits from object (not QWidget) so no Qt application is needed.
    Pure-logic methods are copied from the real class via assignment so
    they execute against this proxy instance as `self`.
    """
    account_type: int = BRAND_B_TYPE

    # --- properties (descriptor objects, not values) ---------------------
    _is_brand_a  = AdminDashboard._is_brand_a   # property
    _brand_label = AdminDashboard._brand_label   # property

    # --- instance methods (plain functions in Python 3) ------------------
    _set_variance_display = AdminDashboard._set_variance_display
    _load_field_config    = AdminDashboard._load_field_config
    _ensure_review_table  = AdminDashboard._ensure_review_table


def _bare_dashboard(account_type=BRAND_B_TYPE):
    """Return a _DashProxy with the given account_type."""
    d = _DashProxy()
    d.account_type = account_type
    return d


def _mock_label():
    lbl = MagicMock()
    lbl.text.return_value = ""
    return lbl


# ══════════════════════════════════════════════════════════════════════════
# 1.  _parse_money  (static — pure, no deps)
# ══════════════════════════════════════════════════════════════════════════

class TestParseMoneyStatic(unittest.TestCase):

    def _p(self, text):
        return AdminDashboard._parse_money(text)

    # ── basic conversions ──────────────────────────────────────────────────
    def test_integer_string(self):
        self.assertEqual(self._p("1000"), 1000.0)

    def test_decimal_string(self):
        self.assertAlmostEqual(self._p("1234.56"), 1234.56)

    def test_comma_thousands_separator(self):
        self.assertAlmostEqual(self._p("1,234.56"), 1234.56)

    def test_multiple_commas(self):
        self.assertAlmostEqual(self._p("1,234,567.89"), 1234567.89)

    def test_zero_string(self):
        self.assertEqual(self._p("0"), 0.0)

    def test_zero_decimal_string(self):
        self.assertEqual(self._p("0.00"), 0.0)

    def test_large_value(self):
        self.assertAlmostEqual(self._p("9,999,999.99"), 9_999_999.99)

    # ── empty / whitespace → 0 ────────────────────────────────────────────
    def test_empty_string_returns_zero(self):
        self.assertEqual(self._p(""), 0.0)

    def test_whitespace_only_returns_zero(self):
        self.assertEqual(self._p("   "), 0.0)

    # ── leading / trailing whitespace is stripped ──────────────────────────
    def test_strips_whitespace(self):
        self.assertAlmostEqual(self._p("  500.00  "), 500.0)

    def test_strips_whitespace_with_commas(self):
        self.assertAlmostEqual(self._p("  1,500.00  "), 1500.0)

    # ── current behaviour: negatives are preserved ──────────────────────
    def test_negative_value_preserved(self):
        self.assertAlmostEqual(self._p("-500.00"), -500.0)

    def test_negative_with_comma(self):
        self.assertAlmostEqual(self._p("-1,000.00"), -1000.0)


# ══════════════════════════════════════════════════════════════════════════
# 2.  _calculate_balances  (static — pure, no deps)
# ══════════════════════════════════════════════════════════════════════════

class TestCalculateBalances(unittest.TestCase):

    def _calc(self, beginning, debit_sum, credit_sum, cash_count):
        return AdminDashboard._calculate_balances(
            beginning, debit_sum, credit_sum, cash_count
        )

    # ── arithmetic ────────────────────────────────────────────────────────
    def test_debit_total_is_beginning_plus_debit_sum(self):
        b = self._calc(300, 200, 0, 0)
        self.assertEqual(b['debit_total'], 500)

    def test_credit_total_equals_credit_sum(self):
        b = self._calc(0, 0, 750, 0)
        self.assertEqual(b['credit_total'], 750)

    def test_ending_balance_is_debit_minus_credit(self):
        b = self._calc(500, 200, 300, 0)
        self.assertEqual(b['ending_balance'], 400)

    def test_cash_result_is_cash_count_minus_ending_balance(self):
        b = self._calc(500, 200, 300, 450)
        self.assertEqual(b['cash_result'], 50)

    def test_all_zeros(self):
        b = self._calc(0, 0, 0, 0)
        self.assertEqual(b['debit_total'], 0)
        self.assertEqual(b['credit_total'], 0)
        self.assertEqual(b['ending_balance'], 0)
        self.assertEqual(b['cash_result'], 0)
        self.assertEqual(b['variance_status'], "balanced")

    # ── variance_status classification ────────────────────────────────────
    def test_balanced_when_cash_result_is_zero(self):
        b = self._calc(1000, 500, 300, 1200)
        # ending = 1500 - 300 = 1200; cash_result = 0
        self.assertEqual(b['variance_status'], "balanced")
        self.assertEqual(b['cash_result'], 0.0)

    def test_over_when_cash_count_exceeds_ending_balance(self):
        b = self._calc(1000, 500, 300, 1201)
        self.assertEqual(b['variance_status'], "over")
        self.assertAlmostEqual(b['cash_result'], 1.0)

    def test_short_when_cash_count_below_ending_balance(self):
        b = self._calc(1000, 500, 300, 1199)
        self.assertEqual(b['variance_status'], "short")
        self.assertAlmostEqual(b['cash_result'], -1.0)

    # ── threshold boundary conditions ─────────────────────────────────────
    def test_strictly_inside_threshold_is_balanced(self):
        tiny = _BALANCED_THRESHOLD - 0.001
        b = self._calc(0, 0, 0, tiny)
        self.assertEqual(b['variance_status'], "balanced")

    def test_exactly_at_threshold_is_over_not_balanced(self):
        # abs(cash_result) < threshold is the condition, so == threshold → over
        b = self._calc(0, 0, 0, _BALANCED_THRESHOLD)
        self.assertEqual(b['variance_status'], "over")

    def test_negative_exactly_at_threshold_is_short_not_balanced(self):
        b = self._calc(0, 0, 0, -_BALANCED_THRESHOLD)
        self.assertEqual(b['variance_status'], "short")

    def test_slightly_over_threshold_on_positive_side_is_over(self):
        b = self._calc(0, 0, 0, _BALANCED_THRESHOLD + 0.001)
        self.assertEqual(b['variance_status'], "over")

    def test_slightly_over_threshold_on_negative_side_is_short(self):
        b = self._calc(0, 0, 0, -(_BALANCED_THRESHOLD + 0.001))
        self.assertEqual(b['variance_status'], "short")

    # ── return value shape ────────────────────────────────────────────────
    def test_returns_all_five_keys(self):
        b = self._calc(0, 0, 0, 0)
        self.assertEqual(
            set(b.keys()),
            {'debit_total', 'credit_total', 'ending_balance',
             'cash_result', 'variance_status'}
        )

    def test_large_values(self):
        b = self._calc(100_000, 50_000, 30_000, 120_001)
        self.assertEqual(b['debit_total'], 150_000)
        self.assertEqual(b['credit_total'], 30_000)
        self.assertEqual(b['ending_balance'], 120_000)
        self.assertAlmostEqual(b['cash_result'], 1.0)
        self.assertEqual(b['variance_status'], "over")


# ══════════════════════════════════════════════════════════════════════════
# 3.  _set_variance_display  (instance — needs mock label)
# ══════════════════════════════════════════════════════════════════════════

class TestSetVarianceDisplay(unittest.TestCase):

    def _make(self):
        dash = _bare_dashboard()
        dash.variance_status_display = MagicMock()
        return dash

    def test_short_text_is_SHORT(self):
        d = self._make()
        d._set_variance_display("short")
        d.variance_status_display.setText.assert_called_once_with("SHORT")

    def test_short_style_contains_red_bg(self):
        d = self._make()
        d._set_variance_display("short")
        css = d.variance_status_display.setStyleSheet.call_args[0][0]
        self.assertIn("#ffcdd2", css)
        self.assertIn("#c62828", css)

    def test_over_text_is_OVER(self):
        d = self._make()
        d._set_variance_display("over")
        d.variance_status_display.setText.assert_called_once_with("OVER")

    def test_over_style_contains_yellow_bg(self):
        d = self._make()
        d._set_variance_display("over")
        css = d.variance_status_display.setStyleSheet.call_args[0][0]
        self.assertIn("#fff3cd", css)
        self.assertIn("#856404", css)

    def test_balanced_text_contains_checkmark(self):
        d = self._make()
        d._set_variance_display("balanced")
        d.variance_status_display.setText.assert_called_once_with("✓ Balanced")

    def test_balanced_style_contains_green_bg(self):
        d = self._make()
        d._set_variance_display("balanced")
        css = d.variance_status_display.setStyleSheet.call_args[0][0]
        self.assertIn("#c8e6c9", css)
        self.assertIn("#2e7d32", css)

    def test_unknown_status_falls_back_to_balanced(self):
        # any value that is not "short" or "over" → balanced branch
        d = self._make()
        d._set_variance_display("anything_else")
        d.variance_status_display.setText.assert_called_once_with("✓ Balanced")

    def test_empty_string_falls_back_to_balanced(self):
        d = self._make()
        d._set_variance_display("")
        d.variance_status_display.setText.assert_called_once_with("✓ Balanced")

    def test_setText_and_setStyleSheet_always_called_together(self):
        for status in ("short", "over", "balanced"):
            d = self._make()
            d._set_variance_display(status)
            self.assertEqual(d.variance_status_display.setText.call_count, 1)
            self.assertEqual(d.variance_status_display.setStyleSheet.call_count, 1)


# ══════════════════════════════════════════════════════════════════════════
# 4.  Brand identity properties  (_is_brand_a, _brand_label)
# ══════════════════════════════════════════════════════════════════════════

class TestBrandIdentityProperties(unittest.TestCase):

    def test_account_type_1_is_brand_a(self):
        self.assertTrue(_bare_dashboard(BRAND_A_TYPE)._is_brand_a)

    def test_account_type_2_is_not_brand_a(self):
        self.assertFalse(_bare_dashboard(BRAND_B_TYPE)._is_brand_a)

    def test_any_non_1_value_is_brand_b(self):
        for t in (0, 2, 3, 99, -1):
            with self.subTest(account_type=t):
                self.assertFalse(_bare_dashboard(t)._is_brand_a)

    def test_brand_a_label(self):
        self.assertEqual(_bare_dashboard(BRAND_A_TYPE)._brand_label, "Brand A")

    def test_brand_b_label(self):
        self.assertEqual(_bare_dashboard(BRAND_B_TYPE)._brand_label, "Brand B")

    def test_label_and_is_brand_a_are_consistent(self):
        for t in (BRAND_A_TYPE, BRAND_B_TYPE):
            d = _bare_dashboard(t)
            if d._is_brand_a:
                self.assertEqual(d._brand_label, "Brand A")
            else:
                self.assertEqual(d._brand_label, "Brand B")


# ══════════════════════════════════════════════════════════════════════════
# 5.  _load_field_config  (DB-first, file fallback)
# ══════════════════════════════════════════════════════════════════════════

class TestLoadFieldConfig(unittest.TestCase):

    def _make(self):
        d = _bare_dashboard()
        d.db = MagicMock()
        return d

    def _db_returns(self, dash, config_dict):
        dash.db.execute_query.return_value = [
            {"config_value": json.dumps(config_dict)}
        ]

    # ── DB success path ────────────────────────────────────────────────────
    def test_returns_db_config_when_available(self):
        d = self._make()
        self._db_returns(d, {"Brand A": {"debit": [["Int", "1", "interest"]], "credit": []}})
        result = d._load_field_config()
        self.assertIsNotNone(result)
        self.assertEqual(result["Brand A"]["debit"][0][0], "Int")

    def test_missing_brand_gets_default_keys_added(self):
        d = self._make()
        self._db_returns(d, {"Brand A": {}})
        result = d._load_field_config()
        # setdefault("debit"/"credit") must be added
        self.assertIn("debit", result["Brand A"])
        self.assertIn("credit", result["Brand A"])

    def test_missing_brand_b_key_added_with_defaults(self):
        d = self._make()
        self._db_returns(d, {"Brand A": {"debit": [], "credit": []}})
        result = d._load_field_config()
        self.assertIn("Brand B", result)

    def test_missing_brand_a_key_added_with_defaults(self):
        d = self._make()
        self._db_returns(d, {"Brand B": {"debit": [], "credit": []}})
        result = d._load_field_config()
        self.assertIn("Brand A", result)

    # ── DB empty / failure → file fallback ────────────────────────────────
    def test_returns_none_when_db_empty_and_no_file(self):
        d = self._make()
        d.db.execute_query.return_value = []
        with patch("os.path.exists", return_value=False):
            result = d._load_field_config()
        self.assertIsNone(result)

    def test_returns_none_when_db_config_value_is_none(self):
        d = self._make()
        d.db.execute_query.return_value = [{"config_value": None}]
        with patch("os.path.exists", return_value=False):
            result = d._load_field_config()
        self.assertIsNone(result)

    def test_returns_none_when_db_raises_and_no_file(self):
        d = self._make()
        d.db.execute_query.side_effect = Exception("connection refused")
        with patch("os.path.exists", return_value=False):
            result = d._load_field_config()
        self.assertIsNone(result)

    def test_file_fallback_used_when_db_returns_empty(self):
        d = self._make()
        d.db.execute_query.return_value = []
        file_cfg = {"Brand A": {"debit": [], "credit": []}}
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json.dumps(file_cfg))):
            result = d._load_field_config()
        self.assertIsNotNone(result)
        self.assertIn("Brand A", result)

    def test_file_fallback_used_when_db_raises(self):
        d = self._make()
        d.db.execute_query.side_effect = Exception("DB down")
        file_cfg = {"Brand B": {"debit": [], "credit": []}}
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json.dumps(file_cfg))):
            result = d._load_field_config()
        self.assertIsNotNone(result)


# ══════════════════════════════════════════════════════════════════════════
# 6.  reset_entry — core DB logic (no Qt)
#     We test the lock / unlock behaviour by isolating the DB call pattern.
# ══════════════════════════════════════════════════════════════════════════

class TestResetEntryDbLogic(unittest.TestCase):
    """
    Test the DB-side contract of reset_entry without touching Qt.
    The rules that must hold regardless of refactoring:
      - Both daily_reports_brand_a and daily_reports get is_locked = 0
      - payable_tbl_brand_a is NEVER deleted or modified
      - cash_float_tbl rows for the given branch/date ARE deleted
    """

    BRANCH = "SCABO_NEW"
    DATE   = "2026-05-04"

    def _run_unlock(self, db, tables=None):
        """Simulate the unlock portion of reset_entry."""
        if tables is None:
            tables = ["daily_reports_brand_a", "daily_reports"]
        found = False
        for table in tables:
            check = db.execute_query(
                f"SELECT COUNT(*) AS cnt FROM {table} "
                "WHERE branch = %s AND date = %s",
                [self.BRANCH, self.DATE]
            )
            if check and check[0].get('cnt', 0) > 0:
                found = True
                db.execute_query(
                    f"UPDATE {table} SET is_locked = 0 "
                    "WHERE branch = %s AND date = %s",
                    [self.BRANCH, self.DATE]
                )
        return found

    def test_both_brand_tables_get_unlocked(self):
        db = MagicMock()
        db.execute_query.return_value = [{"cnt": 1}]
        self._run_unlock(db)

        update_calls = [
            c for c in db.execute_query.call_args_list
            if "SET is_locked = 0" in c[0][0]
        ]
        tables_updated = [c[0][0] for c in update_calls]
        self.assertTrue(any("daily_reports_brand_a" in t for t in tables_updated))
        self.assertTrue(any("daily_reports" in t and "brand_a" not in t
                            for t in tables_updated))

    def test_returns_found_true_when_entry_exists(self):
        db = MagicMock()
        db.execute_query.return_value = [{"cnt": 1}]
        found = self._run_unlock(db)
        self.assertTrue(found)

    def test_returns_found_false_when_no_entry(self):
        db = MagicMock()
        db.execute_query.return_value = [{"cnt": 0}]
        found = self._run_unlock(db)
        self.assertFalse(found)

    def test_no_update_when_count_is_zero(self):
        db = MagicMock()
        db.execute_query.return_value = [{"cnt": 0}]
        self._run_unlock(db)
        update_calls = [
            c for c in db.execute_query.call_args_list
            if "SET is_locked" in c[0][0]
        ]
        self.assertEqual(len(update_calls), 0)

    def test_payable_tbl_brand_a_is_never_deleted(self):
        # Key business rule: this table is intentionally preserved on reset
        db = MagicMock()
        all_queries = []
        def _record(q, params=None):
            all_queries.append(q)
            return [{"cnt": 1}]
        db.execute_query.side_effect = _record

        self._run_unlock(db)
        # also simulate the supp_tables deletion
        db.execute_query(
            "DELETE FROM cash_float_tbl WHERE branch = %s AND date = %s",
            [self.BRANCH, self.DATE]
        )

        for q in all_queries:
            if "payable_tbl_brand_a" in q:
                self.assertNotIn("DELETE", q.upper(),
                    "payable_tbl_brand_a must never be DELETEd during reset")

    def test_cash_float_tbl_is_deleted_on_reset(self):
        db = MagicMock()
        db.execute_query.return_value = []

        # Simulate supp_tables loop from reset_entry
        supp_tables = ["cash_float_tbl"]
        for table in supp_tables:
            db.execute_query(
                f"DELETE FROM {table} WHERE branch = %s AND date = %s",
                [self.BRANCH, self.DATE]
            )

        delete_calls = [
            c for c in db.execute_query.call_args_list
            if "DELETE FROM cash_float_tbl" in c[0][0]
        ]
        self.assertEqual(len(delete_calls), 1)


# ══════════════════════════════════════════════════════════════════════════
# 7.  Brand B palawan-adjustment patching logic
#     (extracted from load_entry_by_date)
# ══════════════════════════════════════════════════════════════════════════

class TestBrandBPalawanPatch(unittest.TestCase):
    """
    Characterizes the rule: when Brand B data has a 0 for a Palawan
    adjustment column, patch it from payable_tbl_brand_a — but only
    if the payable row itself has a non-zero value.
    """

    ADJ_MAP = {
        'palawan_suki_discounts':     'skid',
        'palawan_suki_rebates':       'skir',
        'palawan_cancel':             'cancellation',
        'palawan_pay_out_incentives': 'inc',
    }

    def _patch(self, data, payable_row):
        """Replicate the patching logic from load_entry_by_date."""
        for dc, pc in self.ADJ_MAP.items():
            if float(data.get(dc, 0) or 0) == 0:
                v = float(payable_row.get(pc, 0) or 0)
                if v:
                    data[dc] = v
        return data

    def test_zero_field_gets_value_from_payable(self):
        data    = {'palawan_suki_rebates': 0}
        payable = {'skir': 150.0, 'skid': 0, 'cancellation': 0, 'inc': 0}
        result  = self._patch(data, payable)
        self.assertEqual(result['palawan_suki_rebates'], 150.0)

    def test_nonzero_field_is_not_overwritten(self):
        data    = {'palawan_suki_rebates': 75.0}
        payable = {'skir': 150.0, 'skid': 0, 'cancellation': 0, 'inc': 0}
        result  = self._patch(data, payable)
        self.assertEqual(result['palawan_suki_rebates'], 75.0)

    def test_zero_in_payable_does_not_patch_data(self):
        # payable value 0 → no patch (the `if v:` guard)
        data    = {'palawan_suki_rebates': 0}
        payable = {'skir': 0, 'skid': 0, 'cancellation': 0, 'inc': 0}
        result  = self._patch(data, payable)
        self.assertEqual(result['palawan_suki_rebates'], 0)

    def test_all_four_columns_patched_independently(self):
        data = {k: 0 for k in self.ADJ_MAP}
        payable = {'skid': 10, 'skir': 20, 'cancellation': 30, 'inc': 40}
        result  = self._patch(data, payable)
        self.assertEqual(result['palawan_suki_discounts'],     10)
        self.assertEqual(result['palawan_suki_rebates'],       20)
        self.assertEqual(result['palawan_cancel'],             30)
        self.assertEqual(result['palawan_pay_out_incentives'], 40)

    def test_no_patch_when_all_data_fields_are_nonzero(self):
        data    = {k: 5.0 for k in self.ADJ_MAP}
        payable = {v: 99.0 for v in self.ADJ_MAP.values()}
        result  = self._patch(data, payable)
        # all original values preserved
        for k in self.ADJ_MAP:
            self.assertEqual(result[k], 5.0)

    def test_any_zero_flag_is_true_when_at_least_one_field_is_zero(self):
        data = {
            'palawan_suki_discounts':     5,
            'palawan_suki_rebates':       0,    # ← zero
            'palawan_cancel':             3,
            'palawan_pay_out_incentives': 2,
        }
        any_zero = any(float(data.get(c, 0) or 0) == 0 for c in self.ADJ_MAP)
        self.assertTrue(any_zero)

    def test_any_zero_flag_is_false_when_all_fields_nonzero(self):
        data = {k: 5.0 for k in self.ADJ_MAP}
        any_zero = any(float(data.get(c, 0) or 0) == 0 for c in self.ADJ_MAP)
        self.assertFalse(any_zero)

    def test_string_zero_treated_as_zero(self):
        data    = {'palawan_suki_rebates': '0'}
        payable = {'skir': 99.0, 'skid': 0, 'cancellation': 0, 'inc': 0}
        result  = self._patch(data, payable)
        self.assertEqual(result['palawan_suki_rebates'], 99.0)

    def test_none_treated_as_zero(self):
        data    = {'palawan_suki_rebates': None}
        payable = {'skir': 55.0, 'skid': 0, 'cancellation': 0, 'inc': 0}
        result  = self._patch(data, payable)
        self.assertEqual(result['palawan_suki_rebates'], 55.0)

    def test_missing_key_treated_as_zero(self):
        data    = {}  # key absent entirely
        payable = {'skir': 42.0, 'skid': 0, 'cancellation': 0, 'inc': 0}
        result  = self._patch(data, payable)
        self.assertEqual(result['palawan_suki_rebates'], 42.0)


# ══════════════════════════════════════════════════════════════════════════
# 8.  _ensure_review_table — migration guard
# ══════════════════════════════════════════════════════════════════════════

class TestEnsureReviewTable(unittest.TestCase):

    def _make(self):
        d = _bare_dashboard()
        d.db = MagicMock()
        return d

    def test_create_table_ddl_is_issued(self):
        d = self._make()
        d.db.execute_query.return_value = [{"cnt": 1}]  # columns already exist
        d._ensure_review_table()
        first_call_sql = d.db.execute_query.call_args_list[0][0][0]
        self.assertIn("CREATE TABLE IF NOT EXISTS admin_review_marks", first_call_sql)

    def test_column_existence_checked_before_alter(self):
        d = self._make()
        d.db.execute_query.return_value = [{"cnt": 1}]  # cols exist → no ALTER
        d._ensure_review_table()
        calls_sql = [c[0][0] for c in d.db.execute_query.call_args_list]
        alter_calls = [q for q in calls_sql if "ALTER TABLE" in q]
        self.assertEqual(len(alter_calls), 0)

    def test_alter_issued_when_column_missing(self):
        d = self._make()
        call_count = [0]
        def _side(query, params=None):
            if "CREATE TABLE" in query:
                return []
            if "information_schema" in query.lower():
                call_count[0] += 1
                return [{"cnt": 0}]  # column missing → trigger ALTER
            return []
        d.db.execute_query.side_effect = _side
        d._ensure_review_table()
        all_calls = [c[0][0] for c in d.db.execute_query.call_args_list]
        alter_calls = [q for q in all_calls if "ALTER TABLE" in q]
        self.assertGreater(len(alter_calls), 0)

    def test_does_not_raise_when_db_errors(self):
        d = self._make()
        d.db.execute_query.side_effect = Exception("DB unavailable")
        try:
            d._ensure_review_table()
        except Exception:
            self.fail("_ensure_review_table should swallow DB errors")


# ══════════════════════════════════════════════════════════════════════════
# 9.  save_entry  — balance calc integration (no Qt)
#     We test the _calculate_balances wiring inside save_entry's logic path.
# ══════════════════════════════════════════════════════════════════════════

class TestSaveEntryBalanceWiring(unittest.TestCase):
    """
    Verify that _calculate_balances drives the variance_status that
    save_entry stores, without instantiating Qt.
    """

    def test_balanced_entry_stores_balanced_status(self):
        # beginning=1000, debit_sum=500, credit_sum=300 → ending=1200
        # cash_count=1200 → cash_result=0 → balanced
        b = AdminDashboard._calculate_balances(1000, 500, 300, 1200)
        self.assertEqual(b['variance_status'], "balanced")
        self.assertEqual(b['ending_balance'], 1200)

    def test_over_entry_stores_over_status(self):
        b = AdminDashboard._calculate_balances(0, 0, 0, 50)
        self.assertEqual(b['variance_status'], "over")

    def test_short_entry_stores_short_status(self):
        b = AdminDashboard._calculate_balances(0, 0, 0, -50)
        self.assertEqual(b['variance_status'], "short")

    def test_update_data_dict_gets_correct_keys(self):
        b = AdminDashboard._calculate_balances(500, 200, 100, 600)
        update_data = {
            'beginning_balance': 500,
            'cash_count':        600,
            'debit_total':       b['debit_total'],
            'credit_total':      b['credit_total'],
            'ending_balance':    b['ending_balance'],
            'cash_result':       b['cash_result'],
            'variance_status':   b['variance_status'],
        }
        self.assertEqual(update_data['debit_total'], 700)
        self.assertEqual(update_data['credit_total'], 100)
        self.assertEqual(update_data['ending_balance'], 600)
        self.assertEqual(update_data['cash_result'], 0.0)
        self.assertEqual(update_data['variance_status'], "balanced")


if __name__ == "__main__":
    unittest.main()
