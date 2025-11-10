from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime

def _coerce_price(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0

def _normalize_duration(minutes: int) -> str:
    """Convert minutes into 'Hh Mm' string."""
    if minutes <= 0:
        return "0h 00m"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins:02d}m"

def parse_flights(response_blob: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normalize a single route response (offline or real) into the public schema:
    {
        "origin": "...", "target": "...", "depart": "YYYY-MM-DD",
        "airline": "...", "price": 123.45, "duration": "10h 35m",
        "stops": 0, "flight_number": "XX1234"
    }
    """
    meta = response_blob.get("meta", {})
    legs = response_blob.get("legs", [])
    results: List[Dict[str, Any]] = []

    for leg in legs:
        # Each leg is a single flight option
        out = {
            "origin": meta.get("origin", ""),
            "target": meta.get("target", ""),
            "depart": meta.get("depart", ""),
            "airline": leg.get("airline", "Unknown"),
            "price": _coerce_price(leg.get("price")),
            "duration": _normalize_duration(int(leg.get("duration_minutes", 0))),
            "stops": int(leg.get("stops", 0)),
            "flight_number": leg.get("flight_number", "N/A"),
            "fetched_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "currency": leg.get("currency", meta.get("currency", "USD")),
        }
        results.append(out)

    return results