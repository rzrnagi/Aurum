import logging

import mlflow

from config import MLFLOW_TRACKING_URI, FEATURE_COLS
from db import load_feature_store
from splits import make_splits
from models.arima import train_arima
from models.lgbm import train_lgbm
from models.tft import train_tft

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def print_benchmark(results: dict[str, dict]) -> None:
    header = f"{'Model':<25} {'Val MAE':>10} {'Val Dir%':>10} {'1d MAE':>10} {'1d Dir%':>10} {'5d MAE':>10} {'21d MAE':>10}"
    log.info("\n" + header)
    log.info("-" * len(header))
    for name, r in results.items():
        val_mae  = f"{r['val_mae']:.5f}"              if "val_mae"              in r else "   —   "
        val_dir  = f"{r['val_direction_acc']*100:.1f}%" if "val_direction_acc"  in r else "   —   "
        mae_1d   = f"{r.get('test_mae', r.get('h1_mae', float('nan'))):.5f}"
        dir_1d   = f"{r.get('test_direction_acc', r.get('h1_direction_acc', float('nan')))*100:.1f}%"
        mae_5d   = f"{r['h5_mae']:.5f}"  if "h5_mae"  in r else "   —   "
        mae_21d  = f"{r['h21_mae']:.5f}" if "h21_mae" in r else "   —   "
        log.info(f"{name:<25} {val_mae:>10} {val_dir:>10} {mae_1d:>10} {dir_1d:>10} {mae_5d:>10} {mae_21d:>10}")


def main() -> None:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("finsignal")

    log.info("Loading feature store...")
    df = load_feature_store()
    log.info(f"Loaded {len(df)} rows")

    train, val, test = make_splits(df)
    log.info(
        f"Split — train: {len(train)} ({train['date'].min().date()} → {train['date'].max().date()})  "
        f"val: {len(val)}  test: {len(test)}"
    )

    results = {}

    log.info("Training ARIMA...")
    results["ARIMA(5,0,0)"] = train_arima(train, val, test)

    log.info("Training LightGBM...")
    results["LightGBM"] = train_lgbm(train, val, test)

    # LightGBM + sentiment (only if sentiment data is available)
    has_sentiment = df["sentiment_score"].notna().sum() > 100
    if has_sentiment:
        log.info("Training LightGBM + Sentiment...")
        sentiment_cols = FEATURE_COLS + ["sentiment_score"]
        results["LightGBM+Sentiment"] = train_lgbm(
            train, val, test, run_name="LightGBM+Sentiment", extra_features=["sentiment_score"]
        )
    else:
        log.info("Skipping LightGBM+Sentiment — run sentiment service first")

    log.info("Training TFT (multi-horizon)...")
    results["TFT"] = train_tft(train, val, test)

    print_benchmark(results)
    log.info("Done. Run: mlflow ui --backend-store-uri sqlite:////home/nagi/work/Aurum/mlflow.db")


if __name__ == "__main__":
    main()
