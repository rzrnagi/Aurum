import pandas as pd
import yfinance as yf
from fredapi import Fred
from config import FRED_API_KEY

fred = Fred(api_key=FRED_API_KEY)


def fetch_yfinance(ticker: str, start: str) -> list[dict]:
    """Download OHLCV data for a yfinance ticker from start date to today."""
    df = yf.download(ticker, start=start, auto_adjust=True, progress=False)
    if df.empty:
        return []

    # yfinance 0.2.x sometimes returns a MultiIndex even for single tickers
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    ticker_name = ticker.lstrip("^")

    records = []
    for _, row in df.iterrows():
        records.append({
            "ticker": ticker_name,
            "date": row["Date"].date(),
            "open": float(row["Open"]) if pd.notna(row["Open"]) else None,
            "high": float(row["High"]) if pd.notna(row["High"]) else None,
            "low": float(row["Low"]) if pd.notna(row["Low"]) else None,
            "close": float(row["Close"]) if pd.notna(row["Close"]) else None,
            "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else None,
        })
    return records


def fetch_fred(series_id: str, start: str) -> list[dict]:
    """Download a FRED series from start date. Value stored in close column."""
    series = fred.get_series(series_id, observation_start=start).dropna()
    return [
        {
            "ticker": series_id,
            "date": ts.date(),
            "open": None,
            "high": None,
            "low": None,
            "close": float(value),
            "volume": None,
        }
        for ts, value in series.items()
    ]
