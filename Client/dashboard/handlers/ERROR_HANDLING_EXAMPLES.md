# Server Error Handling Guide

## Overview

The `ServerErrorHandler` and `ServerDownDialog` provide a unified way to handle server connection errors throughout the application.

## Components

### 1. ServerDownDialog
- **Location**: `Client/dashboard/dialogs/server_down_dialog.py`
- **Purpose**: Shows user-friendly error dialog when server is down
- **Buttons**: Retry, Proceed Offline, Exit

### 2. ServerErrorHandler
- **Location**: `Client/dashboard/handlers/error_handler.py`
- **Purpose**: Detects and handles server errors with appropriate user actions
- **Features**: 
  - Automatic error type detection
  - Offline mode support
  - Signal emission for user choices

---

## Usage Examples

### Example 1: Basic API Call with Error Handling

```python
try:
    result = self.db_manager.execute_query(
        "SELECT * FROM daily_reports WHERE date = %s",
        (selected_date,)
    )
except Exception as e:
    choice = self.error_handler.handle_server_error(e)
    if choice == "offline":
        self.offline_mode = True
        logger.info("Switched to offline mode")
        # Reload UI or use cached data
    elif choice == "retry":
        # Retry the operation
        return self.retry_operation()
    else:  # "exit"
        self.close()
    return None
```

### Example 2: During Data Posting

```python
def _post_report(self, selected_date, brand_full, all_vals):
    """Post report with error handling."""
    try:
        # Attempt database insert
        result, err = self.post_handler.post_to_database_with_retry(
            query, values
        )
        
        if err:
            # Error occurred during posting
            choice = self.error_handler.handle_server_error(err)
            if choice == "offline":
                # Save to offline cache instead
                self.offline_manager.cache_report(selected_date, all_vals)
                self._show_message("Report saved offline", "Success")
            return
            
    except Exception as e:
        logger.error(f"Post operation failed: {e}")
        choice = self.error_handler.handle_server_error(e)
```

### Example 3: On Application Startup

```python
def __init__(self, username, branch, corporation, db_manager, offline_mode=False):
    super().__init__()
    
    # ... initialization code ...
    
    self.error_handler = ServerErrorHandler(self, self.offline_manager)
    
    # Try to connect on startup
    try:
        self._verify_database_connection()
    except Exception as e:
        if self.error_handler.is_server_down_error(e):
            choice = self.error_handler.handle_server_error(e)
            if choice == "offline":
                self.offline_mode = True
                self._show_offline_ui()
            else:
                self.close()
```

### Example 4: Using Signal Callbacks

```python
from Client.dashboard.dialogs import ServerDownDialog

dialog = ServerDownDialog(parent=self, show_offline=True)
dialog.retry_clicked.connect(self._retry_operation)
dialog.offline_clicked.connect(self._enable_offline_mode)
dialog.exit_clicked.connect(self.close)

result = dialog.exec_()
```

### Example 5: Checking Error Type

```python
def handle_api_error(self, error, operation_name=""):
    """Handle any API error."""
    
    if self.error_handler.is_server_down_error(error):
        # Server is down - show special dialog
        choice = self.error_handler.handle_server_error(error)
    else:
        # Generic error - show normal message box
        QMessageBox.critical(self, "Error", str(error))
```

---

## Error Detection

The handler automatically detects server-down errors by checking for these indicators:

- `connection refused`
- `connection reset`
- `unable to connect`
- `no route to host`
- `network unreachable`
- `host unreachable`
- `connection timeout`
- `socket timeout`
- HTTP error codes: `502`, `503`, `504`
- Custom messages: `server down`, `server unavailable`

---

## Dialog Flow

```
User tries to connect to server
         ↓
  Connection fails
         ↓
  ErrorHandler detects it's a server-down error
         ↓
  ServerDownDialog shows with 3 options:
         ↓
    ┌────┴─────┬──────────────┐
    ↓          ↓              ↓
  Retry    Proceed Offline   Exit
    ↓          ↓              ↓
 Retry    Enable offline    Close app
 request   mode & continue
```

---

## Best Practices

### 1. **Wrap Database Operations**
```python
try:
    result = self.db_manager.execute_query(...)
except Exception as e:
    self.error_handler.handle_server_error(e)
```

### 2. **Handle User Choice**
```python
choice = self.error_handler.handle_server_error(error)
if choice == "offline":
    # Switch to offline mode
elif choice == "retry":
    # Retry the operation
else:
    # User chose to exit
```

### 3. **Show Offline Indicator**
When offline mode is active, display a visual indicator:
```python
if self.offline_mode:
    self._show_offline_banner()
    # Disable server-dependent features
```

### 4. **Cache Important Data**
Before going offline, ensure data is cached:
```python
if not self.offline_manager.has_cached_data(date):
    self.offline_manager.cache_report(date, data)
```

---

## Testing

To test the dialog without a real server error:

```python
from Client.dashboard.dialogs import ServerDownDialog

# Show dialog directly
dialog = ServerDownDialog(show_offline=True)
result = dialog.exec_()

# Or use the static method
choice = ServerDownDialog.show_and_get_action(
    parent=self,
    show_offline=True
)
print(f"User chose: {choice}")
```

---

## Integration Checklist

- [x] Import `ServerErrorHandler` in core.py
- [x] Initialize `self.error_handler` in `__init__`
- [ ] Wrap database calls with try/except
- [ ] Call `self.error_handler.handle_server_error(e)`
- [ ] Handle user choice (retry/offline/exit)
- [ ] Show offline UI when switching to offline mode
- [ ] Test error dialog appearance
- [ ] Test offline mode fallback
- [ ] Test retry mechanism
