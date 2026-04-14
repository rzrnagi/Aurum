import pandas as pd
from datetime import date
from sqlalchemy import create_engine, text
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)


def get_latest_features(ticker: str = "GSPC") -> pd.Series | None:
    """Return the most recent feature row for a ticker."""
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM feature_store WHERE ticker = :t ORDER BY date DESC LIMIT 1"),
            {"t": ticker},
        ).mappings().fetchone()
    return pd.Series(dict(row)) if row else None


def log_prediction(
    model_name: str,
    model_version: str,
    ticker: str,
    forecast_date: date,
    horizon_days: int,
    predicted_return: float,
    confidence_lower: float,
    confidence_upper: float,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO prediction_log
                    (model_name, model_version, ticker, forecast_date, horizon_days,
                     predicted_return, confidence_lower, confidence_upper)
                VALUES
                    (:model_name, :model_version, :ticker, :forecast_date, :horizon_days,
                     :predicted_return, :confidence_lower, :confidence_upper)
            """),
            {
                "model_name": model_name,
                "model_version": model_version,
                "ticker": ticker,
                "forecast_date": forecast_date,
                "horizon_days": horizon_days,
                "predicted_return": predicted_return,
                "confidence_lower": confidence_lower,
                "confidence_upper": confidence_upper,
            },
        )
