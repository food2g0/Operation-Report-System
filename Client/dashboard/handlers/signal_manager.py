"""Signal manager - handles all PyQt5 signal/slot connections."""

import logging

logger = logging.getLogger(__name__)


class SignalBindingManager:
    """Manages all signal/slot connections in the dashboard."""

    def __init__(self):
        """Initialize signal manager."""
        self._connections = []

    def connect(self, signal, slot, description=""):
        """Register a signal-slot connection."""
        try:
            signal.connect(slot)
            self._connections.append((signal, slot, description))
            if description:
                logger.debug(f"Connected signal: {description}")
        except Exception as e:
            logger.error(f"Failed to connect signal {description}: {e}")

    def block_all_signals(self, widgets):
        """Block signals on a list of widgets."""
        for widget in widgets:
            try:
                if hasattr(widget, "blockSignals"):
                    widget.blockSignals(True)
            except Exception as e:
                logger.error(f"Failed to block signals on widget: {e}")

    def unblock_all_signals(self, widgets):
        """Unblock signals on a list of widgets."""
        for widget in widgets:
            try:
                if hasattr(widget, "blockSignals"):
                    widget.blockSignals(False)
            except Exception as e:
                logger.error(f"Failed to unblock signals on widget: {e}")

    def disconnect_all(self):
        """Disconnect all registered connections."""
        for signal, slot, description in self._connections:
            try:
                signal.disconnect(slot)
                if description:
                    logger.debug(f"Disconnected signal: {description}")
            except Exception as e:
                logger.warning(f"Failed to disconnect signal {description}: {e}")
        self._connections.clear()

    def connect_input_field_signals(self, input_dict, callback, description_prefix=""):
        """Connect signals from a dictionary of input fields."""
        count = 0
        for label, widget in input_dict.items():
            try:
                if hasattr(widget, "textChanged"):
                    signal = widget.textChanged
                    desc = f"{description_prefix} {label}" if description_prefix else label
                    self.connect(signal, callback, desc)
                    count += 1
            except Exception as e:
                logger.warning(f"Failed to connect {label}: {e}")
        return count

    def batch_connect_text_changed(self, field_list, callback, description=""):
        """Connect multiple fields to same callback."""
        count = 0
        for field in field_list:
            try:
                self.connect(field.textChanged, callback, f"{description} field")
                count += 1
            except Exception as e:
                logger.warning(f"Failed to connect field: {e}")
        return count
