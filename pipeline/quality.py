"""DATA QUALITY: stop the pipeline if the data looks wrong."""
import pandas as pd


class DataQualityError(Exception):
    pass


def check(df: pd.DataFrame) -> None:
    problems = []

    if df.empty:
        problems.append("DataFrame is empty")
    if df[["city", "observed_at"]].isnull().any().any():
        problems.append("Null values in city/observed_at")
    if df.duplicated(subset=["city", "observed_at"]).any():
        problems.append("Duplicate (city, observed_at) rows")
    if not df["temperature_c"].dropna().between(-60, 60).all():
        problems.append("temperature_c outside -60..60")
    if not df["humidity_pct"].dropna().between(0, 100).all():
        problems.append("humidity_pct outside 0..100")
    if (df["precipitation_mm"].dropna() < 0).any():
        problems.append("Negative precipitation")

    if problems:
        raise DataQualityError("; ".join(problems))
