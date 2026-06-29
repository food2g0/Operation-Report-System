"""
Network safety wrappers - prevent app freezes on slow/dead internet.

All network operations should use these wrappers with short timeouts.
"""

import socket
import logging

logger = logging.getLogger(__name__)

# Global timeout for all socket operations (seconds)
SOCKET_TIMEOUT = 1.0
HTTP_TIMEOUT = 2.0


def safe_socket_check(host="8.8.8.8", port=53, timeout=SOCKET_TIMEOUT):
    """
    Non-blocking socket connectivity check.
    Returns immediately (True/False) — never hangs.

    Args:
        host: Host to connect to (default: Google DNS)
        port: Port to connect to (default: 53)
        timeout: Max seconds to wait (default: 1.0)

    Returns:
        True if connected, False if timeout/error
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.debug(f"safe_socket_check failed: {e}")
        return False


def safe_http_call(func, *args, timeout=HTTP_TIMEOUT, **kwargs):
    """
    Safely wrap HTTP calls with timeout.

    Args:
        func: Function to call (usually requests.get, requests.post, etc.)
        *args: Positional arguments for func
        timeout: Max seconds to wait (default: 2.0)
        **kwargs: Keyword arguments for func (timeout will be set)

    Returns:
        Result of func if succeeds, None if timeout/error
    """
    try:
        kwargs['timeout'] = timeout
        return func(*args, **kwargs)
    except Exception as e:
        logger.debug(f"safe_http_call failed: {e}")
        return None


class TimeoutSocket(socket.socket):
    """Socket that respects timeout from the start."""

    def __init__(self, timeout=SOCKET_TIMEOUT):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.settimeout(timeout)

    def connect_safe(self, address):
        """Connect with guaranteed timeout — never hangs."""
        try:
            self.connect(address)
            return True
        except (socket.timeout, socket.error):
            return False
        finally:
            self.close()
