from datetime import date
import pandas as pd
from sqlalchemy import create_engine, text
from config import DATABASE_URL, REFERENCE_START, REFERENCE_END, CURRENT_WINDOW_DAYS

engine = create_engine(DATABASE_URL)


def load_reference(feature: str) -> pd.Series:
    with engine.connect() as conn:
        rows = conn.execute(text(
            f"SELECT {feature} FROM feature_store "
            f"WHERE ticker = 'GSPC' AND date >= :start AND date < :end AND {feature} IS NOT NULL "
            f"ORDER BY date"
        ), {"start": REFERENCE_START, "end": REFERENCE_END}).fetchall()
    return pd.Series([r[0] for r in rows], dtype=float)


def load_current(feature: str) -> pd.Series:
    with engine.connect() as conn:
        rows = conn.execute(text(
            f"SELECT {feature} FROM feature_store "
            f"WHERE ticker = 'GSPC' AND {feature} IS NOT NULL "
            f"ORDER BY date DESC LIMIT :n"
        ), {"n": CURRENT_WINDOW_DAYS}).fetchall()
    return pd.Series([r[0] for r in rows], dtype=float)


def get_window_dates() -> tuple[date, date, date, date]:
    with engine.connect() as conn:
        cur_dates = conn.execute(text(
            "SELECT MIN(date), MAX(date) FROM ("
            "  SELECT date FROM feature_store WHERE ticker = 'GSPC' ORDER BY date DESC LIMIT :n"
            ") sub"
        ), {"n": CURRENT_WINDOW_DAYS}).fetchone()
    return (
        date.fromisoformat(REFERENCE_START),
        date.fromisoformat(REFERENCE_END),
        cur_dates[0], cur_dates[1],
    )


def log_drift(feature: str, psi: float, ref_start: date, ref_end: date,
              cur_start: date, cur_end: date, alert: bool) -> None:
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO drift_log
                (feature_name, psi_score, reference_window_start, reference_window_end,
                 current_window_start, current_window_end, alert_triggered)
            VALUES
                (:feature, :psi, :rs, :re, :cs, :ce, :alert)
        """), {"feature": feature, "psi": psi, "rs": ref_start, "re": ref_end,
               "cs": cur_start, "ce": cur_end, "alert": alert})
