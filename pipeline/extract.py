"""EXTRACT: download raw JSON from the APIs and save it untouched."""
import json
import logging
import time
from datetime import date
from pathlib import Path

import requests

from pipeline import config

log = logging.getLogger(__name__)


def fetch_json(url: str, params: dict, retries: int = 3) -> dict:
    """GET a URL and return JSON. Retries with a growing wait if it fails."""
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as err:
            log.warning("Attempt %s/%s failed: %s", attempt, retries, err)
            if attempt == retries:
                raise
            time.sleep(2 ** attempt)


def extract_all(run_date: date) -> Path:
    """Fetch weather + air quality for every city. Returns the folder of raw files."""
    out_dir = config.RAW_DIR / run_date.isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)

    for city, (lat, lon) in config.CITIES.items():
        common = {"latitude": lat, "longitude": lon, "timezone": "UTC",
                  "past_days": 1, "forecast_days": 1}

        weather = fetch_json(config.WEATHER_URL, {**common, "hourly": config.WEATHER_FIELDS})
        air = fetch_json(config.AIR_URL, {**common, "hourly": config.AIR_FIELDS})

        (out_dir / f"{city}_weather.json").write_text(json.dumps(weather))
        (out_dir / f"{city}_air.json").write_text(json.dumps(air))
        log.info("Extracted %s", city)

    return out_dir
