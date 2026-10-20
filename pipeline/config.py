"""Settings for the pipeline. Add or remove cities here."""
from pathlib import Path

# city name -> (latitude, longitude)
CITIES = {
    "Hyderabad": (17.3850, 78.4867),
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
}

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

WEATHER_FIELDS = "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation"
AIR_FIELDS = "pm10,pm2_5,us_aqi"

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
DB_PATH = BASE_DIR / "data" / "warehouse.duckdb"
