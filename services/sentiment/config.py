import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.environ["DATABASE_URL"]
FINNHUB_API_KEY: str = os.environ["FINNHUB_API_KEY"]

# SPY is the ETF proxy Finnhub supports for S&P 500 news
FINNHUB_TICKER = "SPY"

# FinBERT label → numeric score
LABEL_MAP = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}

# Max headlines to score per day (CPU inference is slow)
MAX_HEADLINES_PER_DAY = 10
