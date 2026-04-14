"""
Backfill historical PSI scores into drift_log.
Computes PSI monthly from 2020-01-01 to today, using a 63-day trailing window
as the "current" window at each point in time.
Run once: python backfill.py
"""
import logging
from datetime import date, timedelta
import pandas as pd
from sqlalchemy import create_engine, text
from psi import compute_psi
from config import DATABASE_URL, REFERENCE_START, REFERENCE_END, MONITORED_FEATURES, PSI_ALERT

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL)
WINDOW_DAYS = 63


def load_feature_at(feature: str, window_end: date) -> pd.Series:
    window_start = window_end - timedelta(days=WINDOW_DAYS * 2)  # extra buffer for trading days
    with engine.connect() as conn:
        rows = conn.execute(text(
            f"SELECT {feature} FROM feature_store "
            f"WHERE ticker = 'GSPC' AND date <= :end AND date >= :start "
            f"AND {feature} IS NOT NULL ORDER BY date DESC LIMIT :n"
        ), {"end": window_end, "start": window_start, "n": WINDOW_DAYS}).fetchall()
    return pd.Series([r[0] for r in rows], dtype=float)


def load_reference(feature: str) -> pd.Series:
    with engine.connect() as conn:
        rows = conn.execute(text(
            f"SELECT {feature} FROM feature_store "
            f"WHERE ticker = 'GSPC' AND date >= :start AND date < :end "
            f"AND {feature} IS NOT NULL ORDER BY date"
        ), {"start": REFERENCE_START, "end": REFERENCE_END}).fetchall()
    return pd.Series([r[0] for r in rows], dtype=float)


def insert_drift_row(feature: str, psi: float, ref_start: date, ref_end: date,
                     cur_start: date, cur_end: date, alert: bool, ts) -> None:
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO drift_log
                (feature_name, psi_score, reference_window_start, reference_window_end,
                 current_window_start, current_window_end, alert_triggered, detection_time)
            VALUES
                (:feature, :psi, :rs, :re, :cs, :ce, :alert, :ts)
        """), {"feature": feature, "psi": psi, "rs": ref_start, "re": ref_end,
               "cs": cur_start, "ce": cur_end, "alert": alert, "ts": ts})


def monthly_dates(start: date, end: date):
    d = start
    while d <= end:
        yield d
        # advance ~1 month
        month = d.month + 1 if d.month < 12 else 1
        year = d.year if d.month < 12 else d.year + 1
        d = date(year, month, 1)


def main():
    ref_start = date.fromisoformat(REFERENCE_START)
    ref_end = date.fromisoformat(REFERENCE_END)

    # Pre-load all reference series
    references = {f: load_reference(f) for f in MONITORED_FEATURES}

    backfill_start = date(2020, 1, 1)
    backfill_end = date.today()

    dates = list(monthly_dates(backfill_start, backfill_end))
    log.info(f"Backfilling {len(dates)} monthly snapshots from {backfill_start} to {backfill_end}")

    for snapshot_date in dates:
        for feature in MONITORED_FEATURES:
            current = load_feature_at(feature, snapshot_date)
            if len(current) < 10:
                continue
            ref = references[feature]
            if len(ref) < 30:
                continue

            psi = compute_psi(ref.values, current.values)
            alert = psi >= PSI_ALERT
            cur_start = snapshot_date - timedelta(days=WINDOW_DAYS * 2)

            insert_drift_row(
                feature=feature, psi=psi,
                ref_start=ref_start, ref_end=ref_end,
                cur_start=cur_start, cur_end=snapshot_date,
                alert=alert,
                ts=f"{snapshot_date} 12:00:00+00:00",
            )

        log.info(f"Backfilled {snapshot_date}")

    log.info("Done.")


if __name__ == "__main__":
    main()
