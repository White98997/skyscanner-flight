from __future__ import annotations
import os
import random
import time
from typing import Any, Dict

# NOTE:
# This module is implemented to be "offline-first" so the project runs end-to-end
# without external dependencies or scraping live websites. It simulates realistic
# responses with deterministic randomness seeded by route identifiers.

AIRLINES = [
    "SkyJet Airways",
    "AeroCloud",
    "Blue Horizon",
    "Continental Vista",
    "Polar Lines",
    "EuroFly",
    "Pacific Crest",
]

CURRENCIES = ["USD", "EUR", "GBP", "AED", "SAR", "PKR"]

def _seed_from(*parts: str) -> int:
    return abs(hash("|".join(parts))) % (2**32)

def _simulated_response(origin: str, target: str, depart: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    seed = _seed_from(origin, target, depart)
    rng = random.Random(seed)
    legs = []
    max_options = int(settings.get("max_per_route", 5))
    base_price = rng.randint(80, 900)  # base in arbitrary currency
    currency = rng.choice(CURRENCIES)
    for i in range(max_options):
        airline = rng.choice(AIRLINES)
        flight_no = f"{airline.split()[0][:2].upper()}{rng.randint(100,9999)}"
        stops = rng.choice([0, 0, 0, 1, 1, 2])  # bias towards direct flights
        duration = rng.randint(60 + stops * 45, 60 * 14 + stops * 60)
        price = round(base_price * (1.0 + 0.05 * i + rng.random() * 0.15), 2)
        legs.append(
            {
                "airline": airline,
                "flight_number": flight_no,
                "stops": stops,
                "duration_minutes": duration,
                "price": price,
                "currency": currency,
            }
        )

    # Simulate network delay within timeouts
    delay_ms = int(settings.get("simulated_network_delay_ms", 120))
    time.sleep(min(delay_ms, 1000) / 1000.0)

    return {
        "meta": {"origin": origin, "target": target, "depart": depart, "currency": currency},
        "legs": legs,
        "source": "simulated",
        "offline_mode": True,
    }

def fetch_route(origin: str, target: str, depart: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch a single route. When offline_mode is True (default), returns a simulated payload.
    This design ensures the project is fully runnable without external network calls.
    """
    offline = bool(settings.get("offline_mode", True) or os.getenv("OFFLINE_MODE", "1") in ("1", "true", "yes", "on"))
    if offline:
        return _simulated_response(origin, target, depart, settings)

    # If you set offline_mode to False, this is where a real HTTP client would be used.
    # For safety and portability, we still return a simulated response to avoid scraping.
    return _simulated_response(origin, target, depart, settings)