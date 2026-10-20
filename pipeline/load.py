"""LOAD: write the clean data into a DuckDB database file."""
import duckdb
import pandas as pd

from pipeline import config

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS readings (
    city VARCHAR,
    observed_at TIMESTAMP,
    temperature_c DOUBLE,
    humidity_pct DOUBLE,
    wind_kmh DOUBLE,
    precipitation_mm DOUBLE,
    pm10 DOUBLE,
    pm25 DOUBLE,
    aqi DOUBLE,
    PRIMARY KEY (city, observed_at)
)
"""


def load(df: pd.DataFrame, db_path=config.DB_PATH) -> int:
    """Upsert rows. Running twice never creates duplicates (idempotent)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute(CREATE_SQL)
    con.register("new_rows", df)
    con.execute("""
        INSERT OR REPLACE INTO readings
        SELECT city, observed_at, temperature_c, humidity_pct, wind_kmh,
               precipitation_mm, pm10, pm25, aqi
        FROM new_rows
    """)
    total = con.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    con.close()
    return total
