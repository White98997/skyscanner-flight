from __future__ import annotations
from typing import Any, Dict, List

def _one(origin: str, target: str, depart: str) -> Dict[str, str]:
    return {"origin": origin, "target": target, "depart": depart}

def build_requests(items: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Expand high-level jobs (one-way / roundtrip / multi) into atomic route requests.
    - One-way: single request
    - Roundtrip: two requests (outbound + inbound) if *_return present
    - Multi-city: one request per stop in 'stops' list
    """
    out: List[Dict[str, str]] = []
    for item in items:
        # One-way
        out.append(_one(item["origin"], item["target"], item["depart"]))

        # Roundtrip
        if all(k in item for k in ("origin_return", "target_return", "depart_return")):
            out.append(_one(item["origin_return"], item["target_return"], item["depart_return"]))

        # Multi-city
        for stop in item.get("stops", []):
            out.append(_one(stop["origin"], stop["target"], stop["depart"]))
    return out