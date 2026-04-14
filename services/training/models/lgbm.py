import logging

import lightgbm as lgb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import mlflow.lightgbm
import numpy as np
import pandas as pd

from metrics import mae, rmse, direction_accuracy
from config import FEATURE_COLS

log = logging.getLogger(__name__)

PARAMS = {
    "n_estimators": 300,
    "learning_rate": 0.02,
    "max_depth": 4,
    "num_leaves": 15,
    "min_child_samples": 50,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_lambda": 1.0,
    "objective": "regression",
    "verbose": -1,
}


def train_lgbm(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    run_name: str = "LightGBM",
    extra_features: list[str] | None = None,
) -> dict:
    cols = FEATURE_COLS + (extra_features or [])
    # For sentiment variant, drop rows where extra features are null
    if extra_features:
        train = train.dropna(subset=extra_features)
        val = val.dropna(subset=extra_features)
        test = test.dropna(subset=extra_features)

    def _xy(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
        return df[cols].astype(float), df["target"].astype(float).values

    X_train, y_train = _xy(train)
    X_val, y_val = _xy(val)
    X_test, y_test = _xy(test)

    with mlflow.start_run(run_name=run_name):
        mlflow.log_params({**PARAMS, "model": run_name, "n_features": len(FEATURE_COLS)})

        model = lgb.LGBMRegressor(**PARAMS)
        model.fit(X_train, y_train, callbacks=[lgb.log_evaluation(0)])

        val_pred = model.predict(X_val)
        test_pred = model.predict(X_test)

        results = {
            "val_mae": mae(y_val, val_pred),
            "val_rmse": rmse(y_val, val_pred),
            "val_direction_acc": direction_accuracy(y_val, val_pred),
            "test_mae": mae(y_test, test_pred),
            "test_rmse": rmse(y_test, test_pred),
            "test_direction_acc": direction_accuracy(y_test, test_pred),
        }
        mlflow.log_metrics(results)

        # Feature importance plot
        fig, ax = plt.subplots(figsize=(10, 8))
        lgb.plot_importance(model, ax=ax, max_num_features=20, importance_type="gain")
        ax.set_title(f"{run_name} — Feature Importance (gain)")
        mlflow.log_figure(fig, "feature_importance.png")
        plt.close(fig)

        mlflow.lightgbm.log_model(model, "model")

        log.info(
            f"{run_name}  val_mae={results['val_mae']:.5f}  "
            f"val_dir={results['val_direction_acc']:.3f}  "
            f"test_mae={results['test_mae']:.5f}  "
            f"test_dir={results['test_direction_acc']:.3f}"
        )

    return results
