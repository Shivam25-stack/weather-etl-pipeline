"""Run the whole pipeline:  python run_pipeline.py"""
import logging
from datetime import date

from pipeline import extract, load, quality, transform

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("pipeline")


def main() -> None:
    today = date.today()
    log.info("Step 1/4: extract")
    raw_dir = extract.extract_all(today)

    log.info("Step 2/4: transform")
    df = transform.transform_all(raw_dir)

    log.info("Step 3/4: data quality checks")
    quality.check(df)

    log.info("Step 4/4: load")
    total = load.load(df)
    log.info("Done. %s new rows processed, %s rows in warehouse.", len(df), total)


if __name__ == "__main__":
    main()
