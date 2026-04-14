import numpy as np
import pandas as pd
from db import load_series
from config import N_LAGS


def _to_df(rows: list[tuple], col: str) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["date", col])


def compute_features() -> pd.DataFrame:
    gspc = _to_df(load_series("GSPC"), "close")
    vix = _to_df(load_series("VIX"), "vix")
    dexcaus = _to_df(load_series("DEXCAUS"), "dexcaus")
    t10y2y = _to_df(load_series("T10Y2Y"), "yield_spread")

    df = gspc.copy()
    df["close"] = df["close"].astype(float)
    df["log_return"] = np.log(df["close"] / df["close"].shift(1))

    for i in range(1, N_LAGS + 1):
        df[f"lag_{i}"] = df["log_return"].shift(i)

    df["rolling_mean_5"] = df["log_return"].rolling(5).mean()
    df["rolling_mean_21"] = df["log_return"].rolling(21).mean()
    df["rolling_std_5"] = df["log_return"].rolling(5).std()
    df["rolling_std_21"] = df["log_return"].rolling(21).std()

    # Merge macro series — forward-fill to cover weekends / FRED release gaps
    df = df.merge(vix, on="date", how="left")
    df = df.merge(dexcaus, on="date", how="left")
    df = df.merge(t10y2y, on="date", how="left")

    for col in ("vix", "dexcaus", "yield_spread"):
        df[col] = df[col].ffill()

    # Drop warmup rows: need lag_20 and a full 21-day rolling window
    df = df.dropna(subset=[f"lag_{N_LAGS}", "rolling_std_21"])
    df = df.drop(columns=["close"]).copy()
    df["ticker"] = "GSPC"

    return df
