import logging
from datetime import date
from sqlalchemy import create_engine, text
from fetcher import fetch_headlines
from scorer import score_headlines
from config import DATABASE_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL)


def get_unscored_dates() -> list[date]:
    """Return dates in feature_store that have no sentiment score yet."""
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT date FROM feature_store WHERE sentiment_score IS NULL ORDER BY date")
        ).fetchall()
    return [r[0] for r in rows]


def update_sentiment(target_date: date, score: float) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE feature_store SET sentiment_score = :score WHERE date = :date"),
            {"score": score, "date": target_date},
        )


def main() -> None:
    log.info("Loading FinBERT pipeline (downloads ~500 MB on first run)...")
    # Trigger model load once before the loop
    from scorer import _get_pipeline
    _get_pipeline()

    dates = get_unscored_dates()
    log.info(f"Found {len(dates)} dates without sentiment scores")

    scored, skipped = 0, 0
    for target_date in dates:
        headlines = fetch_headlines(target_date)
        if not headlines:
            skipped += 1
            continue
        score = score_headlines(headlines)
        if score is not None:
            update_sentiment(target_date, score)
            scored += 1

        if scored % 50 == 0 and scored > 0:
            log.info(f"Progress: {scored} scored, {skipped} skipped (no headlines)")

    log.info(f"Done. Scored: {scored}, skipped: {skipped}")
    log.info(
        "Note: Finnhub free tier provides ~1-2 years of history. "
        "Dates outside that window will have NULL sentiment_score. "
        "The LightGBM+sentiment model trains only on rows where it is non-NULL."
    )


if __name__ == "__main__":
    main()
