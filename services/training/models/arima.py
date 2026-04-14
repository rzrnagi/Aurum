import logging

import mlflow
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

from metrics import mae, rmse, direction_accuracy

log = logging.getLogger(__name__)

ARIMA_ORDER = (5, 0, 0)  # AR(5) on stationary log returns


def train_arima(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
) -> dict:
    train_y = train["log_return"].astype(float).values
    val_y = val["target"].astype(float).values
    test_y = test["target"].astype(float).values

    with mlflow.start_run(run_name="ARIMA"):
        mlflow.log_params({
            "model": "ARIMA",
            "order": str(ARIMA_ORDER),
            "train_end": str(train["date"].max().date()),
            "val_end": str(val["date"].max().date()),
        })

        # Fit on train, forecast val
        fitted = ARIMA(train_y, order=ARIMA_ORDER).fit()
        val_pred = fitted.forecast(steps=len(val_y))

        # Refit on train+val, forecast test
        train_val_y = np.concatenate([train_y, val["log_return"].astype(float).values])
        fitted2 = ARIMA(train_val_y, order=ARIMA_ORDER).fit()
        test_pred = fitted2.forecast(steps=len(test_y))

        results = {
            "val_mae": mae(val_y, val_pred),
            "val_rmse": rmse(val_y, val_pred),
            "val_direction_acc": direction_accuracy(val_y, val_pred),
            "test_mae": mae(test_y, test_pred),
            "test_rmse": rmse(test_y, test_pred),
            "test_direction_acc": direction_accuracy(test_y, test_pred),
        }
        mlflow.log_metrics(results)

        log.info(
            f"ARIMA  val_mae={results['val_mae']:.5f}  "
            f"val_dir={results['val_direction_acc']:.3f}  "
            f"test_mae={results['test_mae']:.5f}  "
            f"test_dir={results['test_direction_acc']:.3f}"
        )

    return results
