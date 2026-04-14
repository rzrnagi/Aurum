import logging

import mlflow

from config import MLFLOW_TRACKING_URI
from db import load_feature_store
from splits import make_splits
from models.arima import train_arima
from models.lgbm import train_lgbm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def print_benchmark(results: dict[str, dict]) -> None:
    header = f"{'Model':<20} {'Val MAE':>10} {'Val Dir%':>10} {'Test MAE':>10} {'Test Dir%':>10}"
    log.info("\n" + header)
    log.info("-" * len(header))
    for name, r in results.items():
        log.info(
            f"{name:<20} "
            f"{r['val_mae']:>10.5f} "
            f"{r['val_direction_acc']*100:>9.1f}% "
            f"{r['test_mae']:>10.5f} "
            f"{r['test_direction_acc']*100:>9.1f}%"
        )


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

    print_benchmark(results)
    log.info("Done. Run `mlflow ui` to explore experiment runs.")


if __name__ == "__main__":
    main()
