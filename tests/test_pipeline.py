import pytest

from pipeline import load, quality, transform

WEATHER = {"hourly": {
    "time": ["2026-10-19T00:00", "2026-10-19T01:00"],
    "temperature_2m": [24.0, 23.5], "relative_humidity_2m": [60, 62],
    "wind_speed_10m": [5.0, 6.0], "precipitation": [0.0, 0.1]}}
AIR = {"hourly": {
    "time": ["2026-10-19T00:00", "2026-10-19T01:00"],
    "pm10": [40.0, 42.0], "pm2_5": [20.0, 21.0], "us_aqi": [70, 72]}}


def test_transform_builds_expected_columns():
    df = transform.build_city_frame("Hyderabad", WEATHER, AIR)
    assert len(df) == 2
    assert {"city", "observed_at", "temperature_c", "pm25", "aqi"} <= set(df.columns)


def test_quality_passes_on_good_data():
    quality.check(transform.build_city_frame("Hyderabad", WEATHER, AIR))


def test_quality_fails_on_bad_humidity():
    df = transform.build_city_frame("Hyderabad", WEATHER, AIR)
    df.loc[0, "humidity_pct"] = 500
    with pytest.raises(quality.DataQualityError):
        quality.check(df)


def test_load_is_idempotent(tmp_path):
    df = transform.build_city_frame("Hyderabad", WEATHER, AIR)
    db = tmp_path / "test.duckdb"
    load.load(df, db)
    total = load.load(df, db)  # run twice
    assert total == 2
