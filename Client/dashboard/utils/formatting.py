"""Formatting utilities for the dashboard."""


def format_currency(amount, decimals=2):
    """Format amount as currency.

    Args:
        amount: Numeric amount
        decimals: Number of decimal places

    Returns:
        str: Formatted currency string
    """
    try:
        val = float(amount or 0)
        return f"{val:,.{decimals}f}"
    except (ValueError, TypeError):
        return "0.00"


def parse_currency(currency_str):
    """Parse currency string to float.

    Args:
        currency_str: Currency string (e.g., "1,234.56")

    Returns:
        float: Parsed amount or 0.0 if invalid
    """
    try:
        clean = str(currency_str or "0").replace(",", "").strip()
        return float(clean)
    except (ValueError, TypeError):
        return 0.0


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


def format_date(date_obj, format_str="%Y-%m-%d"):
    """Format date object to string.

    Args:
        date_obj: Date or datetime object
        format_str: Format string

    Returns:
        str: Formatted date string
    """
    try:
        return date_obj.strftime(format_str)
    except (AttributeError, ValueError):
        return ""


def safe_json_serialize(data, field_name="", max_size_kb=100):
    """Safely serialize data to JSON with size limits.

    Args:
        data: Data to serialize
        field_name: Field name for logging
        max_size_kb: Maximum size in kilobytes

    Returns:
        str: JSON string or raises ValueError
    """
    import json
    try:
        json_str = json.dumps(data)
        size_kb = len(json_str.encode()) / 1024
        if size_kb > max_size_kb:
            raise ValueError(f"{field_name} exceeds {max_size_kb}KB limit ({size_kb:.1f}KB)")
        return json_str
    except (TypeError, ValueError) as e:
        raise ValueError(f"Cannot serialize {field_name}: {e}")
