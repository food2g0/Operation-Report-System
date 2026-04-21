

from PyQt5.QtWidgets import QApplication


def _screen_factor() -> float:
    """Return 1.0 for >= 1040 px high screens, 0.62 for <= 768, linear between."""
    try:
        screen = QApplication.primaryScreen()
        if screen:
            h = screen.availableGeometry().height()
            if h >= 1040:
                return 1.0
            if h <= 768:
                return 0.62
            return 0.62 + (h - 768) / (1040 - 768) * 0.38
    except Exception:
        pass
    return 1.0


_SCL = None


def _sz(px: int) -> int:
    """Scale a *design* pixel value (1080p baseline) to current screen."""
    global _SCL
    if _SCL is None:
        _SCL = _screen_factor()
    return max(1, round(px * _SCL))
