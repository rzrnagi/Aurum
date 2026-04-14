import time
from datetime import date, timedelta
import finnhub
from config import FINNHUB_API_KEY, FINNHUB_TICKER

client = finnhub.Client(api_key=FINNHUB_API_KEY)


def fetch_headlines(target_date: date) -> list[str]:
    """
    Fetch news headlines for target_date.
    Finnhub free tier provides recent data only (~1-2 years history).
    Returns empty list for dates outside the available window.
    """
    from_dt = target_date.strftime("%Y-%m-%d")
    to_dt = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        news = client.company_news(FINNHUB_TICKER, _from=from_dt, to=to_dt)
        time.sleep(0.1)  # stay under 60 req/min free tier limit
        return [item["headline"] for item in news if "headline" in item]
    except Exception:
        return []
