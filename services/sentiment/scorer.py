from transformers import pipeline
from config import LABEL_MAP, MAX_HEADLINES_PER_DAY

_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        # Downloads ~500 MB on first run
        _pipeline = pipeline(
            "text-classification",
            model="ProsusAI/finbert",
            truncation=True,
            max_length=512,
        )
    return _pipeline


def score_headlines(headlines: list[str]) -> float | None:
    """
    Score a list of headlines with FinBERT.
    Returns confidence-weighted mean sentiment in [-1, 1], or None if no headlines.
    """
    if not headlines:
        return None

    scorer = _get_pipeline()
    scores = []
    for headline in headlines[:MAX_HEADLINES_PER_DAY]:
        result = scorer(headline)[0]
        label = result["label"].lower()
        scores.append(LABEL_MAP.get(label, 0.0) * result["score"])

    return sum(scores) / len(scores)
