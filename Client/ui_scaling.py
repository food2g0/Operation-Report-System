from PyQt5.QtWidgets import QApplication


def _screen_factor() -> float:
    """Return a scale factor relative to the 1920×1080 design baseline.

    Floor is 0.82 so that the smallest fonts (_sz(11) → 9 px) stay
    legible on 1366×768 monitors.  Previously 0.62 was used, which
    produced 7 px labels — too small to read.
    """
    try:
        screen = QApplication.primaryScreen()
        if screen:
            h = screen.availableGeometry().height()
            if h >= 1040:
                return 1.0
            if h <= 768:
                return 0.82
            # Linear interpolation 768 → 0.82, 1040 → 1.0
            return 0.82 + (h - 768) / (1040 - 768) * 0.18
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


def reset_scale() -> None:
    """Force re-detection of screen factor (call after a screen change)."""
    global _SCL
    _SCL = None
