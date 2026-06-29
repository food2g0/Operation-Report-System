

_BALANCED_THRESHOLD = 0.01


def parse_money(text: str) -> float:
    """Parse a money input string to float, stripping commas and whitespace."""
    return float(text.strip().replace(',', '') or 0)


def calculate_balances(
    beginning: float,
    debit_sum: float,
    credit_sum: float,
    cash_count: float,
) -> dict:

    debit_total    = beginning + debit_sum
    credit_total   = credit_sum
    ending_balance = debit_total - credit_total
    cash_result    = cash_count - ending_balance

    if abs(cash_result) < _BALANCED_THRESHOLD:
        variance_status = "balanced"
    elif cash_result > 0:
        variance_status = "over"
    else:
        variance_status = "short"

    return {
        "debit_total":     debit_total,
        "credit_total":    credit_total,
        "ending_balance":  ending_balance,
        "cash_result":     cash_result,
        "variance_status": variance_status,
    }
