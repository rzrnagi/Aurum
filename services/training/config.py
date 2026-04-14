import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.environ["DATABASE_URL"]
MLFLOW_TRACKING_URI: str = os.environ.get(
    "MLFLOW_TRACKING_URI", "file:///home/nagi/work/Aurum/mlruns"
)

TRAIN_END = "2020-01-01"
VAL_END = "2022-01-01"
# Test: 2022-01-01 to present

FEATURE_COLS = (
    [f"lag_{i}" for i in range(1, 21)]
    + ["rolling_mean_5", "rolling_mean_21", "rolling_std_5", "rolling_std_21"]
    + ["vix", "dexcaus", "yield_spread"]
)
