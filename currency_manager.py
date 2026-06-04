"""
Currency Manager - Centralized database currency management
Allows SuperAdmin to add/remove/update currencies without updating client code
"""

import logging
from api_db_manager import APIDbManager

logger = logging.getLogger("CurrencyManager")

# Prefer direct DB manager when running on the server (superadmin process).
# Fall back to API-based manager when running in client context or when
# direct DB manager is not importable.
try:
    from db_connect_pooled import db_manager as direct_db_manager
except Exception:
    direct_db_manager = None

# API manager used as fallback
api_db_manager = APIDbManager()


def _exec(sql, params=None):
    """Execute SQL using the direct DB manager when available, otherwise
    route through the API DB manager. Returns the result or raises.
    """
    # Try direct DB first (server process)
    if direct_db_manager is not None:
        try:
            return direct_db_manager.execute_query(sql, params)
        except Exception:
            # fall through to API manager
            logger.debug("Direct DB execution failed, falling back to API manager")
    # Use API manager
    return api_db_manager.execute_query(sql, params)


# Default currencies to initialize if table is empty
DEFAULT_CURRENCIES = [
    "USD - US Dollar",
    "EUR - Euro",
    "JPY - Japanese Yen",
    "KRW - Korean Won",
    "CNY - Chinese Yuan",
    "SGD - Singapore Dollar",
    "AED - UAE Dirham",
    "SAR - Saudi Riyal",
    "AUD - Australian Dollar",
    "CAD - Canadian Dollar",
    "GBP - British Pound",
    "HKD - Hong Kong Dollar",
    "CHF - Swiss Franc",
    "NOK - Norwegian Krone",
    "SEK - Swedish Krona",
    "THB - Thai Baht",
    "MYR - Malaysian Ringgit",
    "IDR - Indonesian Rupiah",
    "VND - Vietnamese Dong",
    "TWD - Taiwan Dollar"
]


def init_currencies_table():
    """Initialize the currencies table with default values if needed"""
    try:
        # Create table if it doesn't exist
        create_sql = """
        CREATE TABLE IF NOT EXISTS currencies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            currency_name VARCHAR(100) NOT NULL UNIQUE,
            description VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_active (is_active)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        _exec(create_sql)
        logger.info("Currencies table initialized")
        
        # Check if table is empty
        result = _exec("SELECT COUNT(*) as count FROM currencies")
        if result and result[0]['count'] == 0:
            # Insert default currencies
            for currency in DEFAULT_CURRENCIES:
                add_currency(currency)
            logger.info(f"Inserted {len(DEFAULT_CURRENCIES)} default currencies")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing currencies table: {e}")
        # Try to add is_active column if it doesn't exist (for legacy installations)
        try:
            _exec("ALTER TABLE currencies ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            logger.info("Added is_active column to currencies table")
        except:
            pass
        return False


def get_all_currencies(active_only=True):
    """Get all currencies from database
    
    Args:
        active_only: If True, only return active currencies
        
    Returns:
        List of currency names
    """
    try:
        if active_only:
            sql = "SELECT currency_name FROM currencies WHERE is_active = TRUE ORDER BY currency_name ASC"
        else:
            sql = "SELECT currency_name FROM currencies ORDER BY currency_name ASC"
        
        result = _exec(sql)
        if result:
            return [row['currency_name'] for row in result]
        return []
    except Exception as e:
        logger.error(f"Error fetching currencies: {e}")
        return DEFAULT_CURRENCIES  # Fallback to defaults


def add_currency(currency_name, description=""):
    """Add a new currency to the database
    
    Args:
        currency_name: Name of the currency (e.g., "USD - US Dollar")
        description: Optional description
        
    Returns:
        True if successful, False otherwise
    """
    try:
        sql = """
        INSERT INTO currencies (currency_name, description, is_active)
        VALUES (%s, %s, TRUE)
        """
        _exec(sql, (currency_name, description))
        logger.info(f"Added currency: {currency_name}")
        return True
    except Exception as e:
        logger.error(f"Error adding currency '{currency_name}': {e}")
        return False


def remove_currency(currency_name):
    """Remove a currency (soft delete - mark as inactive)
    
    Args:
        currency_name: Name of the currency to remove
        
    Returns:
        True if successful, False otherwise
    """
    try:
        sql = "UPDATE currencies SET is_active = FALSE WHERE currency_name = %s"
        _exec(sql, (currency_name,))
        logger.info(f"Removed currency: {currency_name}")
        return True
    except Exception as e:
        logger.error(f"Error removing currency '{currency_name}': {e}")
        return False


def restore_currency(currency_name):
    """Restore a previously removed currency (mark as active)
    
    Args:
        currency_name: Name of the currency to restore
        
    Returns:
        True if successful, False otherwise
    """
    try:
        sql = "UPDATE currencies SET is_active = TRUE WHERE currency_name = %s"
        _exec(sql, (currency_name,))
        logger.info(f"Restored currency: {currency_name}")
        return True
    except Exception as e:
        logger.error(f"Error restoring currency '{currency_name}': {e}")
        return False


def currency_exists(currency_name):
    """Check if a currency exists in the database
    
    Args:
        currency_name: Name of the currency to check
        
    Returns:
        True if exists, False otherwise
    """
    try:
        sql = "SELECT COUNT(*) as count FROM currencies WHERE currency_name = %s"
        result = _exec(sql, (currency_name,))
        if result:
            return result[0]['count'] > 0
        return False
    except Exception as e:
        logger.error(f"Error checking currency: {e}")
        return False


def get_all_currencies_with_status():
    """Get all currencies including inactive ones with their status
    
    Returns:
        List of dicts with 'currency_name' and 'is_active' keys
    """
    try:
        sql = "SELECT currency_name, is_active FROM currencies ORDER BY is_active DESC, currency_name ASC"
        result = _exec(sql)
        if result:
            return result
        return []
    except Exception as e:
        logger.error(f"Error fetching currencies with status: {e}")
        return []


def update_currency_description(currency_name, description):
    """Update currency description
    
    Args:
        currency_name: Name of the currency
        description: New description
        
    Returns:
        True if successful, False otherwise
    """
    try:
        sql = "UPDATE currencies SET description = %s WHERE currency_name = %s"
        _exec(sql, (description, currency_name))
        logger.info(f"Updated description for currency: {currency_name}")
        return True
    except Exception as e:
        logger.error(f"Error updating currency description: {e}")
        return False
