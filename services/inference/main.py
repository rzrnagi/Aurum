import logging
from datetime import date, datetime
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import DATABASE_URL
from db import get_latest_features, log_prediction
from model_loader import load_model, get_run_metrics
from cache import get_cached, set_cached

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

FEATURE_COLS = (
    ["log_return"]
    + [f"lag_{i}" for i in range(1, 21)]
    + ["rolling_mean_5", "rolling_mean_21", "rolling_std_5", "rolling_std_21"]
    + ["vix", "dexcaus", "yield_spread"]
)

app = FastAPI(
    title="FinSignal Inference API",
    description="S&P 500 log return forecasting",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/predict")
def predict(ticker: str = "GSPC", horizon: int = 1):
    cache_key = f"prediction:{ticker}:{date.today()}:{horizon}"
    cached = get_cached(cache_key)
    if cached:
        cached["cache"] = "hit"
        return cached

    features = get_latest_features(ticker)
    if features is None:
        raise HTTPException(status_code=404, detail=f"No features found for {ticker}")

    model, run_id = load_model("LightGBM")
    X = pd.DataFrame([features[FEATURE_COLS].astype(float)])
    predicted_return = float(model.predict(X)[0])

    # Confidence interval: ±2σ using rolling_std_21 as volatility estimate
    sigma = float(features["rolling_std_21"])
    confidence_lower = predicted_return - 2 * sigma
    confidence_upper = predicted_return + 2 * sigma

    forecast_date = date.today()
    log_prediction(
        model_name="LightGBM",
        model_version=run_id[:8],
        ticker=ticker,
        forecast_date=forecast_date,
        horizon_days=horizon,
        predicted_return=predicted_return,
        confidence_lower=confidence_lower,
        confidence_upper=confidence_upper,
    )

    result = {
        "ticker": ticker,
        "forecast_date": str(forecast_date),
        "horizon_days": horizon,
        "predicted_return": round(predicted_return, 6),
        "confidence_lower": round(confidence_lower, 6),
        "confidence_upper": round(confidence_upper, 6),
        "model": "LightGBM",
        "model_version": run_id[:8],
        "cache": "miss",
    }
    set_cached(cache_key, result)
    return result


@app.get("/models")
def list_models():
    models = []
    for name in ["ARIMA", "LightGBM", "TFT"]:
        metrics = get_run_metrics(name)
        if metrics:
            models.append({"name": name, "metrics": metrics})
    return {"models": models}


@app.get("/drift")
def drift_status():
    # Placeholder — PSI drift monitoring implemented in Phase 6
    return {
        "status": "drift_monitoring_pending",
        "message": "Drift service not yet deployed",
    }
