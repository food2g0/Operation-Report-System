"""
Centralized Logging Configuration
Structured logging with rotation, by module, and multiple outputs.
"""

import os
import sys
import json
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Create logs directory
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Color codes for terminal output
COLORS = {
    "DEBUG": "\033[36m",      # Cyan
    "INFO": "\033[32m",       # Green
    "WARNING": "\033[33m",    # Yellow
    "ERROR": "\033[31m",      # Red
    "CRITICAL": "\033[41m",   # Red background
    "RESET": "\033[0m",       # Reset
}


class ColoredFormatter(logging.Formatter):
    """Add colors to console logs."""

    def format(self, record):
        log_color = COLORS.get(record.levelname, COLORS["RESET"])
        record.levelname = f"{log_color}{record.levelname}{COLORS['RESET']}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "pathname": record.pathname,
            "lineno": record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_logging(app_name: str = "ors", level: str = "INFO"):
    """
    Setup centralized logging for the application.

    Args:
        app_name: Name of the application (for log file naming)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # ── Console Handler (colored) ──────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = ColoredFormatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # ── File Handler (JSON, rotated daily) ─────────────────────────────────────
    file_path = LOG_DIR / f"{app_name}.log"
    file_handler = RotatingFileHandler(
        filename=file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=30,  # Keep 30 days of logs
    )
    file_handler.setLevel(log_level)
    file_formatter = JSONFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # ── Error File Handler (ERROR+ only, rotated) ─────────────────────────────
    error_path = LOG_DIR / f"{app_name}_errors.log"
    error_handler = RotatingFileHandler(
        filename=error_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=30,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)

    root_logger.info(f"Logging initialized: {app_name} at level {level}")
    root_logger.info(f"Logs directory: {LOG_DIR}")

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module."""
    return logging.getLogger(name)
