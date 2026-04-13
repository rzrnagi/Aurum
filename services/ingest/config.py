import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.environ["DATABASE_URL"]
KAFKA_BOOTSTRAP_SERVERS: str = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
FRED_API_KEY: str = os.environ["FRED_API_KEY"]
INGEST_START_DATE: str = os.environ.get("INGEST_START_DATE", "2000-01-01")
KAFKA_TOPIC: str = "raw-market-data"

# tickers fetched via yfinance (^ prefix stripped for DB storage)
YFINANCE_TICKERS: list[str] = ["^GSPC", "^VIX"]

# series fetched via FRED API
FRED_SERIES: list[str] = ["DEXCAUS", "T10Y2Y"]
