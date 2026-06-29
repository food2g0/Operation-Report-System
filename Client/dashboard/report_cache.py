"""
Client-side disk cache for locked daily reports.

Cache layout (Windows):
  %APPDATA%/OperationReportSystem/report_cache/{year}/
      {date}_{brand_slug}_{branch_slug}_{corp_slug}.json

Only locked reports are cached. Cache entries are invalidated automatically
when an admin reset notification arrives.
"""
import os
import sys
import json
import logging
import decimal
import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_CACHE_VERSION = 2   # bump when cache structure changes to auto-discard old files


# ── Helpers ───────────────────────────────────────────────────────────────────

def _base_dir() -> str:
    """Return the writable OperationReportSystem base folder."""
    if getattr(sys, 'frozen', False):
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        return os.path.join(base, 'OperationReportSystem')
    # Dev / source mode: project root
    return str(Path(__file__).parent.parent.parent)


def _slug(s: str) -> str:
    """Make a string filesystem-safe."""
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in str(s))


def _cache_path(date_str: str, brand: str, branch: str, corporation: str) -> str:
    year = date_str[:4]
    folder = os.path.join(_base_dir(), "report_cache", year)
    os.makedirs(folder, exist_ok=True)
    fname = f"{date_str}_{_slug(brand)}_{_slug(branch)}_{_slug(corporation)}.json"
    return os.path.join(folder, fname)


class _Encoder(json.JSONEncoder):
    """Handle DB-native types that are not JSON-serialisable."""
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        return super().default(obj)


# ── Public API ────────────────────────────────────────────────────────────────

def save(date_str: str, brand: str, branch: str, corporation: str, data: dict):
    """Persist *data* (the raw DB row dict) to the local cache."""
    try:
        path = _cache_path(date_str, brand, branch, corporation)
        payload = {
            "v":         _CACHE_VERSION,
            "cached_at": datetime.datetime.utcnow().isoformat(),
            "data":      data,
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, cls=_Encoder, ensure_ascii=False)
        logger.debug("Cache WRITE %s", path)
    except Exception as exc:
        logger.warning("Cache write failed (%s/%s/%s): %s", date_str, brand, branch, exc)


def load(date_str: str, brand: str, branch: str, corporation: str):
    """Return (cached_row_dict, cached_at_iso) or (None, None) on miss."""
    try:
        path = _cache_path(date_str, brand, branch, corporation)
        if not os.path.exists(path):
            return None, None
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if payload.get("v") != _CACHE_VERSION:
            os.remove(path)
            logger.debug("Cache STALE (version mismatch) — discarded: %s", path)
            return None, None
        logger.debug("Cache HIT %s", path)
        return payload["data"], payload.get("cached_at")
    except Exception as exc:
        logger.warning("Cache read failed (%s/%s/%s): %s", date_str, brand, branch, exc)
        return None, None


def invalidate(date_str: str, branch: str, corporation: str):
    """Delete cached entries for all brands on *date_str* (called on admin reset)."""
    year = date_str[:4]
    folder = os.path.join(_base_dir(), "report_cache", year)
    for brand in ("Brand A", "Brand B"):
        path = os.path.join(
            folder,
            f"{date_str}_{_slug(brand)}_{_slug(branch)}_{_slug(corporation)}.json"
        )
        if os.path.exists(path):
            try:
                os.remove(path)
                logger.info("Cache INVALIDATED %s", path)
            except Exception as exc:
                logger.warning("Cache invalidate failed: %s", exc)
