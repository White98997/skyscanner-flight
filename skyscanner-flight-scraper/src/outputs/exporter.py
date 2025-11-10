from __future__ import annotations
import json
from pathlib import Path
from typing import Any, List, Dict
from datetime import datetime

def write_json(records: List[Dict[str, Any]], out_path: Path) -> None:
    payload = {
        "meta": {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "records": len(records),
        },
        "data": records,
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)