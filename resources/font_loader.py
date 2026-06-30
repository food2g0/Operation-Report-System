"""
Font loader — registers bundled Poppins weights with Qt's font database.

Call load_poppins() once after QApplication is created, before any window
is shown. Falls back silently if font files are missing.
"""
import os
import logging

logger = logging.getLogger(__name__)

_FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

_WEIGHTS = [
    "Poppins-Regular.ttf",
    "Poppins-Medium.ttf",
    "Poppins-SemiBold.ttf",
    "Poppins-Bold.ttf",
    "Poppins-ExtraBold.ttf",
]

_loaded = False


def load_poppins() -> bool:
    """Register all Poppins weights. Returns True if at least one loaded."""
    global _loaded
    if _loaded:
        return True

    try:
        from PyQt5.QtGui import QFontDatabase
    except ImportError:
        return False

    ok = 0
    for fname in _WEIGHTS:
        path = os.path.join(_FONTS_DIR, fname)
        if not os.path.isfile(path):
            logger.debug("Font file missing: %s", path)
            continue
        fid = QFontDatabase.addApplicationFont(path)
        if fid >= 0:
            ok += 1
        else:
            logger.warning("Failed to register font: %s", fname)

    _loaded = ok > 0
    if _loaded:
        logger.debug("Poppins loaded (%d/%d weights)", ok, len(_WEIGHTS))
    else:
        logger.warning("No Poppins weights loaded — UI will fall back to Segoe UI")
    return _loaded
