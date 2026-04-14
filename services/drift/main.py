import logging
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from config import MONITORED_FEATURES, PSI_WARNING, PSI_ALERT
from psi import compute_psi
from db import load_reference, load_current, get_window_dates, log_drift

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Prometheus gauges — one per feature
psi_gauge = Gauge("finsignal_psi_score", "PSI drift score", ["feature"])
alert_gauge = Gauge("finsignal_drift_alert", "1 if PSI >= alert threshold", ["feature"])

_latest_results: dict = {}


def run_drift_check() -> dict:
    ref_start, ref_end, cur_start, cur_end = get_window_dates()
    results = {}

    for feature in MONITORED_FEATURES:
        ref = load_reference(feature)
        cur = load_current(feature)

        if len(ref) < 30 or len(cur) < 10:
            log.warning(f"Skipping {feature} — insufficient data")
            continue

        psi = compute_psi(ref.values, cur.values)
        alert = psi >= PSI_ALERT

        psi_gauge.labels(feature=feature).set(psi)
        alert_gauge.labels(feature=feature).set(int(alert))

        log_drift(feature, psi, ref_start, ref_end, cur_start, cur_end, alert)

        status = "ALERT" if alert else ("WARNING" if psi >= PSI_WARNING else "OK")
        log.info(f"{feature:<25} PSI={psi:.4f}  [{status}]")
        results[feature] = {"psi": round(psi, 6), "status": status}

    return results


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run drift check on startup then every hour
    async def periodic():
        while True:
            try:
                _latest_results.update(run_drift_check())
            except Exception as e:
                log.error(f"Drift check failed: {e}")
            await asyncio.sleep(3600)

    task = asyncio.create_task(periodic())
    yield
    task.cancel()


app = FastAPI(title="FinSignal Drift Monitor", lifespan=lifespan)


@app.get("/metrics")
def metrics():
    """Prometheus scrape endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/status")
def status():
    """Latest PSI scores for all monitored features."""
    return {"features": _latest_results}


@app.post("/run")
def trigger_check():
    """Manually trigger a drift check."""
    results = run_drift_check()
    _latest_results.update(results)
    return {"features": results}
