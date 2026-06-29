"""
Entry load / save service.

Target refactor: extracts DB logic from these AdminDashboard methods:
  - load_entry_by_date    (admin/dashboard.py ~L3310)
  - save_entry            (admin/dashboard.py ~L3838)
"""

import logging

from .balance_service import calculate_balances

logger = logging.getLogger(__name__)


def load_entry_data(db, table: str, branch: str, date: str) -> dict | None:
    """
    Fetch a single daily report row by branch + date.

    Returns the row dict, or None if not found.
    Does NOT patch Brand B Palawan adjustments — caller must call
    patch_brand_b_palawan() if needed.
    """
    query = f"SELECT * FROM {table} WHERE branch=%s AND date=%s ORDER BY id DESC LIMIT 1"
    result = db.execute_query(query, [branch, date])
    if not result:
        return None
    return result[0]


def patch_brand_b_palawan(data: dict, db, branch: str, date: str) -> dict:
    """
    For Brand B: when any Palawan adjustment column is 0 in `data`,
    read the non-zero value from payable_tbl_brand_a and patch it in.

    Columns mapped:
      palawan_suki_discounts     → skid
      palawan_suki_rebates       → skir
      palawan_cancel             → cancellation
      palawan_pay_out_incentives → inc
    """
    _adj_map = {
        'palawan_suki_discounts':     'skid',
        'palawan_suki_rebates':       'skir',
        'palawan_cancel':             'cancellation',
        'palawan_pay_out_incentives': 'inc',
    }
    _any_zero = any(float(data.get(c, 0) or 0) == 0 for c in _adj_map)
    if _any_zero:
        try:
            _pr = db.execute_query(
                "SELECT skid, skir, cancellation, inc "
                "FROM payable_tbl_brand_a "
                "WHERE branch=%s AND date=%s LIMIT 1",
                (branch, date)
            )
            if _pr:
                for _dc, _pc in _adj_map.items():
                    if float(data.get(_dc, 0) or 0) == 0:
                        _v = float(_pr[0].get(_pc, 0) or 0)
                        if _v:
                            data[_dc] = _v
        except Exception as _e:
            logger.debug("Palawan adj patch in patch_brand_b_palawan: %s", _e)
    return data


def build_save_payload(
    debit_fields: dict,
    debit_amounts: dict,
    debit_lotes: dict,
    credit_fields: dict,
    credit_amounts: dict,
    credit_lotes: dict,
    beginning: float,
    cash_count: float,
) -> tuple:
    """
    Build the UPDATE payload dict from pre-extracted widget values.

    Args:
        debit_fields:  {ui_label: db_col}
        debit_amounts: {ui_label: float}
        debit_lotes:   {ui_label: int}
        credit_fields: {ui_label: db_col}
        credit_amounts:{ui_label: float}
        credit_lotes:  {ui_label: int}
        beginning:     float
        cash_count:    float

    Returns:
        (update_data: dict, balances: dict)
    """
    update_data = {}
    debit_sum = 0
    for ui_label, db_col in debit_fields.items():
        amount = debit_amounts.get(ui_label, 0)
        lotes = debit_lotes.get(ui_label, 0)
        update_data[db_col] = amount
        update_data[db_col + "_lotes"] = lotes
        debit_sum += amount

    credit_sum = 0
    for ui_label, db_col in credit_fields.items():
        amount = credit_amounts.get(ui_label, 0)
        lotes = credit_lotes.get(ui_label, 0)
        update_data[db_col] = amount
        update_data[db_col + "_lotes"] = lotes
        credit_sum += amount

    balances = calculate_balances(beginning, debit_sum, credit_sum, cash_count)

    update_data['beginning_balance'] = beginning
    update_data['cash_count']        = cash_count
    update_data['debit_total']       = balances['debit_total']
    update_data['credit_total']      = balances['credit_total']
    update_data['ending_balance']    = balances['ending_balance']
    update_data['cash_result']       = balances['cash_result']
    update_data['variance_status']   = balances['variance_status']

    return update_data, balances


def persist_entry(db, table: str, record_id: int, payload: dict) -> int:
    """
    Execute UPDATE on `table` for `record_id`.
    Returns rows_affected.
    """
    set_clauses = []
    values = []
    for col, val in payload.items():
        set_clauses.append(f"`{col}` = %s")
        values.append(val)
    values.append(record_id)

    update_query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE id = %s"
    rows_affected = db.execute_query(update_query, values)
    return rows_affected


def upsert_palawan_payable(db, corporation: str, branch: str, date: str, p_cols: dict) -> None:
    """
    UPSERT Palawan payable data into payable_tbl_brand_a.

    Args:
        db:          database manager instance
        corporation: corporation name string
        branch:      branch name string
        date:        date string (yyyy-MM-dd)
        p_cols:      {col_name: value} dict of columns to upsert
    """
    col_names    = ', '.join(p_cols.keys())
    set_parts    = ', '.join(f"{c}=VALUES({c})" for c in p_cols.keys())
    placeholders = ', '.join(['%s'] * len(p_cols))
    upsert_sql   = (
        "INSERT INTO payable_tbl_brand_a "
        "(corporation, branch, date, " + col_names + ") "
        "VALUES (%s, %s, %s, " + placeholders + ") "
        "ON DUPLICATE KEY UPDATE " + set_parts + ", updated_at=CURRENT_TIMESTAMP"
    )
    try:
        db.execute_query(upsert_sql, [corporation, branch, date] + list(p_cols.values()))
    except Exception as pe:
        logger.error("upsert_palawan_payable: %s", pe)
