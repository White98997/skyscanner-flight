import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List
import importlib.util
import sys

# Configure logging early
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("skyscanner-flight-scraper")

ROOT = Path(__file__).resolve().parent
SRC = ROOT
PROJECT = ROOT.parent

def load_module(module_path: Path, module_name: str):
    """Dynamically load a module by absolute path to avoid package import issues."""
    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} at {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module

# Load internal modules
flight_parser = load_module(ROOT / "extractors" / "flight_parser.py", "flight_parser")
route_builder = load_module(ROOT / "extractors" / "route_builder.py", "route_builder")
date_formatter = load_module(ROOT / "utils" / "date_formatter.py", "date_formatter")
request_handler = load_module(ROOT / "utils" / "request_handler.py", "request_handler")
exporter = load_module(ROOT / "outputs" / "exporter.py", "exporter")

def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_settings(settings_path: Path) -> Dict[str, Any]:
    if not settings_path.exists():
        raise FileNotFoundError(f"Settings file not found: {settings_path}")
    settings = read_json(settings_path)
    # Env overrides
    offline_env = os.getenv("OFFLINE_MODE")
    if offline_env is not None:
        settings["offline_mode"] = offline_env.lower() in ("1", "true", "yes", "on")
    output_path_env = os.getenv("OUTPUT_PATH")
    if output_path_env:
        settings["output_path"] = output_path_env
    return settings

def validate_input(items: List[Dict[str, Any]]) -> None:
    """
    Validate minimal fields for each job item:
      - origin, target, depart (YYYY-MM-DD)
      - Optionals for roundtrip: origin_return, target_return, depart_return
      - Optionals for multi: stops (list of dicts with origin/target/depart)
    """
    for idx, item in enumerate(items):
        if "origin" not in item or "target" not in item or "depart" not in item:
            raise ValueError(f"Item #{idx} missing required keys: origin, target, depart")
        if not date_formatter.is_iso_date(item["depart"]):
            raise ValueError(f"Item #{idx} has invalid 'depart' date: {item['depart']}")
        if "depart_return" in item and not date_formatter.is_iso_date(item["depart_return"]):
            raise ValueError(f"Item #{idx} has invalid 'depart_return' date: {item['depart_return']}")
        if "stops" in item:
            if not isinstance(item["stops"], list):
                raise ValueError(f"Item #{idx} 'stops' must be a list")
            for sidx, stop in enumerate(item["stops"]):
                for key in ("origin", "target", "depart"):
                    if key not in stop:
                        raise ValueError(f"Item #{idx} stop #{sidx} missing '{key}'")
                if not date_formatter.is_iso_date(stop["depart"]):
                    raise ValueError(f"Item #{idx} stop #{sidx} invalid date: {stop['depart']}")

def run(input_path: Path, settings_path: Path) -> int:
    logger.info("Loading settings from %s", settings_path)
    settings = load_settings(settings_path)

    logger.info("Reading input from %s", input_path)
    input_items = read_json(input_path)
    if not isinstance(input_items, list):
        raise ValueError("Input JSON must be a list of route jobs")

    validate_input(input_items)

    logger.info("Building concrete route requests")
    requests = route_builder.build_requests(input_items)

    logger.info("Fetching %d routes (offline_mode=%s)", len(requests), settings.get("offline_mode", True))
    raw_results = []
    for req in requests:
        try:
            response_blob = request_handler.fetch_route(
                origin=req["origin"],
                target=req["target"],
                depart=req["depart"],
                settings=settings,
            )
            raw_results.append(response_blob)
        except Exception as e:
            logger.exception("Failed to fetch route %s -> %s on %s: %s", req["origin"], req["target"], req["depart"], e)

    logger.info("Parsing %d raw responses", len(raw_results))
    parsed: List[Dict[str, Any]] = []
    for blob in raw_results:
        try:
            parsed.extend(flight_parser.parse_flights(blob))
        except Exception as e:
            logger.exception("Failed to parse a response: %s", e)

    # Respect max_results setting
    max_results = settings.get("max_results")
    if isinstance(max_results, int) and max_results > 0:
        parsed = parsed[:max_results]

    output_path = Path(settings.get("output_path", str(PROJECT / "data" / "results.json")))
    logger.info("Writing %d records to %s", len(parsed), output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    exporter.write_json(parsed, output_path)

    logger.info("Done.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Skyscanner Flight Scraper (offline-friendly demo).")
    parser.add_argument(
        "--input",
        default=str(PROJECT / "data" / "sample_input.json"),
        help="Path to input JSON list of route jobs.",
    )
    parser.add_argument(
        "--settings",
        default=str(ROOT / "config" / "settings.example.json"),
        help="Path to settings JSON.",
    )
    args = parser.parse_args()

    try:
        exit_code = run(Path(args.input), Path(args.settings))
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        exit_code = 1

    raise SystemExit(exit_code)

if __name__ == "__main__":
    main()