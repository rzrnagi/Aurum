import logging
from datetime import timedelta
from sqlalchemy.dialects.postgresql import insert
from db import engine, raw_market_data, get_last_date
from fetchers import fetch_yfinance, fetch_fred
from kafka_producer import publish_records
from config import YFINANCE_TICKERS, FRED_SERIES, INGEST_START_DATE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def insert_records(records: list[dict]) -> None:
    with engine.begin() as conn:
        conn.execute(
            insert(raw_market_data)
            .values(records)
            .on_conflict_do_nothing(index_elements=["ticker", "date"])
        )


def run_source(ticker_key: str, fetch_fn, ticker_label: str) -> None:
    last = get_last_date(ticker_label)
    start = (last + timedelta(days=1)).isoformat() if last else INGEST_START_DATE

    records = fetch_fn(ticker_key, start)
    if not records:
        log.info(f"{ticker_label}: already up to date")
        return

    insert_records(records)
    publish_records(records)
    log.info(f"{ticker_label}: ingested and published {len(records)} rows (from {start})")


def main() -> None:
    for ticker in YFINANCE_TICKERS:
        run_source(ticker, fetch_yfinance, ticker.lstrip("^"))

    for series_id in FRED_SERIES:
        run_source(series_id, fetch_fred, series_id)

    log.info("Ingest complete.")


if __name__ == "__main__":
    main()
