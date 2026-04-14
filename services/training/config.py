import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.environ["DATABASE_URL"]
MLFLOW_TRACKING_URI: str = os.environ.get(
    "MLFLOW_TRACKING_URI", "sqlite:////home/nagi/work/Aurum/mlflow.db"
)

TRAIN_START = "2005-01-01"
TRAIN_END = "2020-01-01"
VAL_END = "2022-01-01"
# Test: 2022-01-01 to present

FEATURE_COLS = (
    ["log_return"]  # today's return — lag_0, known at end of trading day
    + [f"lag_{i}" for i in range(1, 21)]
    + ["rolling_mean_5", "rolling_mean_21", "rolling_std_5", "rolling_std_21"]
    + ["vix", "dexcaus", "yield_spread"]
)
