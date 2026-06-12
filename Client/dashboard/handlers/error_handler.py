"""Error handler for server connection issues."""

import logging
from PyQt5.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


class ServerErrorHandler:
    """Handles server connection errors and offline mode."""

    def __init__(self, parent=None, offline_manager=None):
        """Initialize error handler.

        Args:
            parent: Parent widget for dialogs
            offline_manager: Offline manager instance for offline mode support
        """
        self.parent = parent
        self.offline_manager = offline_manager

    def is_server_down_error(self, error):
        """Check if error is a server-down error.

        Args:
            error: Exception or error message

        Returns:
            bool: True if server is down
        """
        error_str = str(error).lower()
        server_down_indicators = [
            'connection refused',
            'connection reset',
            'unable to connect',
            'no route to host',
            'network unreachable',
            'host unreachable',
            'connection timeout',
            'socket timeout',
            '502',  # Bad Gateway
            '503',  # Service Unavailable
            '504',  # Gateway Timeout
            'server down',
            'server unavailable',
            'unreachable',
        ]
        return any(indicator in error_str for indicator in server_down_indicators)

    def handle_server_error(self, error, show_dialog=True):
        """Handle server connection error.

        Args:
            error: Exception or error message
            show_dialog: Whether to show error dialog

        Returns:
            str: User's choice - "retry", "offline", or "exit"
        """
        logger.error(f"Server error: {error}")

        if not self.is_server_down_error(error):
            logger.debug("Error is not a server-down error, skipping special handling")
            return None

        if not show_dialog:
            return "exit"

        # Import here to avoid circular imports
        from Client.dashboard.dialogs import ServerDownDialog

        choice = ServerDownDialog.show_and_get_action(
            self.parent,
            show_offline=self.offline_manager is not None
        )

        logger.info(f"User chose: {choice}")
        return choice

    def handle_api_error(self, error, operation_name="Operation"):
        """Handle API error with user notification.

        Args:
            error: Exception or error message
            operation_name: Name of operation that failed

        Returns:
            str: User's choice
        """
        if self.is_server_down_error(error):
            return self.handle_server_error(error, show_dialog=True)

        # For other errors, show a generic message
        if self.parent:
            QMessageBox.critical(
                self.parent,
                f"{operation_name} Failed",
                f"An error occurred:\n\n{str(error)}\n\n"
                "Please check your connection and try again."
            )
        logger.error(f"API error during {operation_name}: {error}")
        return "exit"

    def enable_offline_mode(self):
        """Enable offline mode for the application.

        Returns:
            bool: True if offline mode enabled successfully
        """
        if not self.offline_manager:
            logger.warning("Offline manager not available")
            return False

        try:
            # Set offline mode flag
            if hasattr(self.offline_manager, 'set_offline_mode'):
                self.offline_manager.set_offline_mode(True)
            logger.info("Offline mode enabled")
            return True
        except Exception as e:
            logger.error(f"Failed to enable offline mode: {e}")
            return False
