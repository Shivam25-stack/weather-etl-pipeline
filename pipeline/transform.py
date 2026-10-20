"""TRANSFORM: turn raw JSON into one clean table."""
import json
from pathlib import Path

import pandas as pd

from pipeline import config


def build_city_frame(city: str, weather: dict, air: dict) -> pd.DataFrame:
    """Combine one city's weather and air-quality JSON into a DataFrame."""
    w = pd.DataFrame(weather["hourly"])
    a = pd.DataFrame(air["hourly"])
    df = w.merge(a, on="time", how="left")

    df = df.rename(columns={
        "time": "observed_at",
        "temperature_2m": "temperature_c",
        "relative_humidity_2m": "humidity_pct",
        "wind_speed_10m": "wind_kmh",
        "precipitation": "precipitation_mm",
        "pm2_5": "pm25",
        "us_aqi": "aqi",
    })
    df["observed_at"] = pd.to_datetime(df["observed_at"])
    df.insert(0, "city", city)
    return df


def transform_all(raw_dir: Path) -> pd.DataFrame:
    """Read every city's raw files from a folder and stack them together."""
    frames = []
    for city in config.CITIES:
        weather = json.loads((raw_dir / f"{city}_weather.json").read_text())
        air = json.loads((raw_dir / f"{city}_air.json").read_text())
        frames.append(build_city_frame(city, weather, air))

    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates(subset=["city", "observed_at"])
    return df
