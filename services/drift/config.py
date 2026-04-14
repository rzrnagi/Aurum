import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.environ["DATABASE_URL"]

# PSI thresholds (industry standard)
PSI_WARNING = 0.1   # moderate shift
PSI_ALERT   = 0.2   # significant shift — trigger alert

# Reference window: training period
REFERENCE_START = "2005-01-01"
REFERENCE_END   = "2020-01-01"

# Current window: last N trading days
CURRENT_WINDOW_DAYS = 63  # ~3 months

# Features to monitor
MONITORED_FEATURES = [
    "log_return", "vix", "yield_spread", "dexcaus",
    "rolling_std_21", "rolling_mean_21",
]
