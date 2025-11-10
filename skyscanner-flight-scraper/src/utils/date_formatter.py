from __future__ import annotations
from datetime import datetime

ISO_FMT = "%Y-%m-%d"

def is_iso_date(value: str) -> bool:
    try:
        datetime.strptime(value, ISO_FMT)
        return True
    except Exception:
        return False

def normalize_date(value: str) -> str:
    """
    Validate and normalize to YYYY-MM-DD, raises on invalid input.
    """
    dt = datetime.strptime(value, ISO_FMT)
    return dt.strftime(ISO_FMT)