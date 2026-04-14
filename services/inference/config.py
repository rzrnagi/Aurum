import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.environ["DATABASE_URL"]
REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
MLFLOW_TRACKING_URI: str = os.environ.get(
    "MLFLOW_TRACKING_URI", "sqlite:////home/nagi/work/Aurum/mlflow.db"
)
CACHE_TTL_SECONDS: int = 3600
