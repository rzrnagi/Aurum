import logging

import lightning.pytorch as pl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
import torch
from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
from pytorch_forecasting.data import GroupNormalizer
from pytorch_forecasting.metrics import MAE as TFT_MAE

from metrics import mae, rmse, direction_accuracy
from config import FEATURE_COLS

log = logging.getLogger(__name__)

ENCODER_LENGTH = 63       # ~3 months of trading days
MAX_PREDICTION_LENGTH = 21
EVAL_HORIZONS = [1, 5, 21]

# Features that are unknown in the future (we cannot observe them ahead of time)
UNKNOWN_REALS = [
    "log_return", "rolling_mean_5", "rolling_mean_21",
    "rolling_std_5", "rolling_std_21", "vix", "dexcaus", "yield_spread",
] + [f"lag_{i}" for i in range(1, 21)]

TFT_PARAMS = {
    "hidden_size": 32,
    "attention_head_size": 2,
    "dropout": 0.1,
    "hidden_continuous_size": 16,
    "learning_rate": 1e-3,
}


def _build_dataset(df: pd.DataFrame, max_time_idx: int) -> TimeSeriesDataSet:
    return TimeSeriesDataSet(
        df[df["time_idx"] <= max_time_idx],
        time_idx="time_idx",
        target="target",
        group_ids=["ticker"],
        min_encoder_length=ENCODER_LENGTH // 2,
        max_encoder_length=ENCODER_LENGTH,
        min_prediction_length=1,
        max_prediction_length=MAX_PREDICTION_LENGTH,
        static_categoricals=["ticker"],
        time_varying_known_reals=["time_idx", "day_of_week", "month"],
        time_varying_unknown_reals=UNKNOWN_REALS + ["target"],
        target_normalizer=GroupNormalizer(groups=["ticker"], transformation="softplus"),
        add_relative_time_idx=True,
        add_target_scales=True,
        add_encoder_length=True,
        allow_missing_timesteps=False,
    )


def _eval_at_horizons(preds: np.ndarray, actuals: np.ndarray) -> dict:
    results = {}
    for h in EVAL_HORIZONS:
        idx = h - 1
        if idx < preds.shape[1]:
            y_pred = preds[:, idx]
            y_true = actuals[:, idx]
            results[f"h{h}_mae"] = mae(y_true, y_pred)
            results[f"h{h}_rmse"] = rmse(y_true, y_pred)
            results[f"h{h}_direction_acc"] = direction_accuracy(y_true, y_pred)
    return results


def train_tft(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
) -> dict:
    # Build unified df with time index and calendar features
    df = pd.concat([train, val, test]).copy().sort_values("date").reset_index(drop=True)
    df["time_idx"] = range(len(df))
    df["day_of_week"] = df["date"].dt.dayofweek.astype(float)
    df["month"] = df["date"].dt.month.astype(float)
    df["ticker"] = df["ticker"].astype(str)

    train_end_idx = df[df["date"] < val["date"].min()]["time_idx"].max()
    val_end_idx = df[df["date"] < test["date"].min()]["time_idx"].max()

    training_dataset = _build_dataset(df, train_end_idx)
    val_dataset = training_dataset.from_dataset(
        training_dataset, df[df["time_idx"] <= val_end_idx], predict=False
    )

    train_loader = training_dataset.to_dataloader(train=True, batch_size=64, num_workers=0)
    val_loader = val_dataset.to_dataloader(train=False, batch_size=64, num_workers=0)

    model = TemporalFusionTransformer.from_dataset(
        training_dataset,
        **TFT_PARAMS,
        loss=TFT_MAE(),
        log_interval=10,
        reduce_on_plateau_patience=3,
    )
    log.info(f"TFT parameters: {sum(p.numel() for p in model.parameters()):,}")

    trainer = pl.Trainer(
        max_epochs=15,
        accelerator="auto",
        enable_progress_bar=True,
        enable_model_summary=False,
        gradient_clip_val=0.1,
        logger=False,
    )

    with mlflow.start_run(run_name="TFT"):
        mlflow.log_params({**TFT_PARAMS, "encoder_length": ENCODER_LENGTH,
                           "max_prediction_length": MAX_PREDICTION_LENGTH, "max_epochs": 15})

        trainer.fit(model, train_dataloaders=train_loader, val_dataloaders=val_loader)

        # Evaluate on test set
        test_dataset = training_dataset.from_dataset(
            training_dataset, df, predict=True, stop_randomization=True
        )
        test_loader = test_dataset.to_dataloader(train=False, batch_size=64, num_workers=0)

        raw_predictions = model.predict(test_loader, return_y=True, trainer_kwargs={"accelerator": "auto"})
        preds = raw_predictions.output.numpy()
        actuals = raw_predictions.y[0].numpy()

        results = _eval_at_horizons(preds, actuals)
        mlflow.log_metrics(results)

        # Attention weights plot (TFT interpretability)
        interpretation = model.interpret_output(
            model.predict(val_loader, mode="raw", return_x=True).output,
            reduction="sum",
        )
        fig, axes = model.plot_interpretation(interpretation)
        mlflow.log_figure(fig, "tft_interpretation.png")
        plt.close(fig)

        log.info(
            f"TFT  1d_mae={results.get('h1_mae', 'N/A'):.5f}  "
            f"1d_dir={results.get('h1_direction_acc', 'N/A'):.3f}  "
            f"5d_mae={results.get('h5_mae', 'N/A'):.5f}  "
            f"21d_mae={results.get('h21_mae', 'N/A'):.5f}"
        )

    return results
