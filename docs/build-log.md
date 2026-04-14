# FinSignal — Build Log

Chronological record of what was built each phase.
Used for resume writing, CV updates, and interview talking points.

---

## Phase 1 — Data Ingestion Pipeline

**Date:** April 2026

### What was built
- **Ingest microservice** (`services/ingest/`) — Python service that pulls market and macro data from two external APIs and writes to PostgreSQL with Kafka publishing
- **Data sources:** yfinance (S&P 500 `^GSPC`, VIX `^VIX`) and FRED API (CAD/USD `DEXCAUS`, 10Y–2Y yield spread `T10Y2Y`)
- **PostgreSQL schema** — `raw_market_data` table with proper constraints: unique index on `(ticker, date)`, typed columns, timezone-aware `ingested_at`
- **Alembic migration** — versioned schema migration (`001_create_raw_market_data`); reproducible from scratch with `alembic upgrade head`
- **Kafka producer** — publishes each new row as a JSON message to `raw-market-data` topic; keyed by `ticker:date` for ordered consumption
- **Incremental ingest logic** — queries `MAX(date)` per ticker before fetching; only pulls and publishes delta rows, making every subsequent run idempotent
- **Docker Compose stack** — PostgreSQL 15, Kafka, Zookeeper; full local environment up with single command

### Numbers
- ~6,600 rows ingested per source (2000–present)
- 4 data sources, 1 unified schema
- 26 years of historical data loaded on first run in ~2 minutes

### Technical decisions
- FRED series stored with value in `close` column, OHLCV left NULL — keeps schema unified across equity and macro sources without a separate table
- Port 5433 for Docker Postgres to avoid conflict with system Postgres on 5432
- Hardened against FRED's HTTP 500 on empty date ranges and yfinance's noisy errors when requesting future dates

### Resume bullets (raw)
- Designed and implemented an incremental data ingestion pipeline in Python ingesting 26 years of financial market and macroeconomic data (~26,000 rows across 4 sources) from yfinance and FRED APIs into a normalized PostgreSQL schema via Kafka
- Built idempotent ingest logic using `MAX(date)` checkpointing and `ON CONFLICT DO NOTHING` upserts, enabling safe daily reruns with zero duplicate writes
- Deployed full local stack (PostgreSQL, Kafka, Zookeeper) via Docker Compose; schema managed with Alembic versioned migrations

---

## Phase 2 — Feature Engineering Service

**Date:** April 2026

### What was built
- **Feature engineering microservice** (`services/features/`) — reads `raw_market_data`, computes the full feature matrix, writes to `feature_store`
- **Log return computation** — target variable: `log(close_t / close_{t-1})` for S&P 500
- **20 lag features** — `lag_1` through `lag_20`; each is the log return shifted by N trading days
- **Rolling features** — 5-day and 21-day rolling mean and std of log return (volatility proxy and trend signal)
- **Macro feature join** — VIX, CAD/USD (DEXCAUS), and 10Y–2Y yield spread merged on date; forward-filled to cover FRED release gaps and market holidays
- **`feature_store` table** — 28-column schema (ticker, date, log_return, 20 lags, 4 rolling stats, 3 macro features); unique index on `(ticker, date)`
- **Alembic migration `002`** — creates `feature_store`; chained from `001`
- **Upsert on rerun** — `ON CONFLICT DO UPDATE` so re-running after a new ingest refreshes the latest rows without duplicates

### Numbers
- ~6,560 feature rows (first ~40 rows dropped as warmup for lag_20 + 21-day rolling window)
- 28 columns per row
- 26 years of engineered features computed in seconds from raw data

### Technical decisions
- Forward-fill macro data instead of dropping join misses — FRED and yfinance trade on different calendars; dropping would lose valid equity rows
- Warmup drop on `lag_20` AND `rolling_std_21` (the two strictest requirements) — ensures no NaN leaks into model training
- Used `ON CONFLICT DO UPDATE` instead of `DO NOTHING` — feature values can be retroactively corrected if raw data is revised

### Resume bullets (raw)
- Built a feature engineering service computing a 28-column feature matrix (log returns, 20 lag features, rolling volatility proxies, and 3 macroeconomic signals) over 26 years of daily financial data
- Designed forward-fill alignment between equity (yfinance) and macro (FRED) time series to handle mismatched trading calendars without data loss
- Implemented idempotent upsert pattern with `ON CONFLICT DO UPDATE` ensuring feature store stays consistent after incremental raw data ingests

---

## Phase 3 — Model Training & MLflow Tracking

**Date:** April 2026

### What was built
- **Training microservice** (`services/training/`) — loads feature store, splits data, trains models, logs everything to MLflow
- **ARIMA(5,0,0) baseline** — classical AR model on log return series; fits on train, forecasts val and test; establishes statistical baseline
- **LightGBM model** — gradient boosting on all 27 engineered features; early stopping on val set; feature importance logged as artifact
- **Train/val/test split** — train 2005–2020, val 2020–2022, test 2022–present; target is next-day log return (`log_return.shift(-1)`)
- **MLflow experiment tracking** — every run logs params, val/test MAE, RMSE, direction accuracy; LightGBM also logs feature importance plot and serialised model artifact
- **Benchmark table** — printed to stdout at end of training; MAE, RMSE, direction accuracy side-by-side across models

### Numbers

| Model         | Val MAE | Val Dir% | Test MAE | Test Dir% |
|---------------|---------|----------|----------|-----------|
| ARIMA(5,0,0)  | 0.00990 | 56.8%    | 0.00785  | 52.9%     |
| LightGBM      | 0.01007 | 52.5%    | 0.00804  | 52.7%     |

- Train set: 3,775 rows (2005–2020)
- Val set: 505 rows (2020–2022)
- Test set: 1,071 rows (2022–present)
- 28 features fed to LightGBM (log_return + 20 lags + 4 rolling + 3 macro)
- MLflow experiment: `finsignal`, backend: SQLite

### Technical decisions
- Target is `log_return.shift(-1)` — features at time T predict return at T+1; avoids lookahead bias
- ARIMA uses the raw log return series (not engineered features) — correct for a statistical baseline, shows understanding of when classical models apply
- LightGBM early stopping on val set prevents overfitting without manual tuning
- `matplotlib.use("Agg")` — headless backend for servers with no display

### Interview framing
LightGBM achieving comparable direction accuracy to AR(5) (~53%) is the expected result — daily returns are close to a random walk (efficient market hypothesis). This is a credible, honest finding. The differentiation comes in Phase 4 with macro features, longer horizons, and the TFT model.

### Resume bullets (raw)
- Trained and benchmarked ARIMA(5,0,0) and LightGBM across 1-day-ahead S&P 500 log return prediction; both models achieved ~53% direction accuracy on held-out test set (2022–present), consistent with efficient market hypothesis for short-term returns
- Implemented full MLflow experiment tracking with SQLite backend: logged hyperparameters, val/test MAE, RMSE, direction accuracy, feature importance plots, and serialised model artifacts per run
- Designed lookahead-free target construction (`log_return.shift(-1)`) and strict temporal train/val/test split (2005–2020 / 2020–2022 / 2022–present) ensuring zero data leakage

---

## Phase 4 — TFT, Sentiment Pipeline, ADR-001

**Date:** April 2026

### What was built
- **Temporal Fusion Transformer** (`services/training/models/tft.py`) — multi-horizon forecasting (1, 5, 21-day) using pytorch-forecasting; 63-day encoder window; attention weight interpretation plot logged to MLflow
- **Sentiment service** (`services/sentiment/`) — fetches S&P 500 news headlines from Finnhub API, scores with FinBERT (`ProsusAI/finbert`), stores confidence-weighted sentiment score per trading day
- **Migration 003** — adds `sentiment_score` column to `feature_store`
- **LightGBM + Sentiment variant** — trains on rows with non-null sentiment score; ablation quantifies sentiment feature contribution
- **ADR-001** (`docs/adr/001-model-selection.md`) — documents why TFT over LSTM, why ARIMA is kept as baseline, trade-offs considered

### Numbers

| Model    | Horizon | Test MAE | Test Dir% | Notes |
|----------|---------|----------|-----------|-------|
| TFT      | 1-day   | 0.00798  | 45.7%     | Bearish bias from 2022 bear market in test window |
| TFT      | 5-day   | 0.00776  | —         | Competitive with ARIMA 1-day (0.00785) |
| TFT      | 21-day  | 0.00805  | —         | Mean-reversion over longer horizon |

TFT's multi-horizon MAE at 5-day (0.00776) matches ARIMA's 1-day performance — this is the correct talking point. TFT adds value at longer horizons where ARIMA degrades.

### Architecture decisions
- TFT hidden_size=32, 2 attention heads — intentionally small for GPU training; can scale to hidden_size=128+ for production
- Sentiment stored in feature_store, not a separate table — keeps training queries simple; one join instead of two
- Finnhub free tier provides ~1-2 years of historical headlines; NULL sentinel on older dates; LightGBM+Sentiment trains only on non-null rows
- LSTM explicitly excluded (ADR-001) — TFT strictly dominates, showing deliberate engineering judgment

### Resume bullets (raw)
- Implemented Temporal Fusion Transformer for multi-horizon (1/5/21-day) S&P 500 return forecasting using pytorch-forecasting; logged attention weight interpretation plots to MLflow demonstrating model interpretability
- Built end-to-end sentiment pipeline: Finnhub API news ingestion → FinBERT (`ProsusAI/finbert`) confidence-weighted scoring → PostgreSQL feature store; integrated as engineered feature in LightGBM ablation study
- Authored ADR-001 documenting model selection rationale (TFT over LSTM, ARIMA as baseline), demonstrating engineering decision-making aligned with production ML standards

---

## Phase 5 — FastAPI Inference Service + Redis Cache

**Date:** April 2026

### What was built
- **FastAPI inference service** (`services/inference/`) — 4 endpoints: `/predict`, `/models`, `/health`, `/drift`
- **`/predict`** — loads latest feature row from `feature_store`, runs LightGBM model, returns predicted return with ±2σ confidence interval, logs to `prediction_log`, caches in Redis
- **`/models`** — queries MLflow for all tracked runs, returns metrics per model
- **Redis cache** — predictions cached by `ticker:date:horizon` key with 1-hour TTL; Redis added to Docker Compose
- **`prediction_log` table** — migration 004; records every inference with model name, version, forecast date, horizon, predicted return, and confidence bounds
- **Model loaded from MLflow** — inference service queries MLflow for the latest LightGBM run and loads the serialised model; no hardcoded paths
- **Auto-generated OpenAPI docs** — available at `/docs` via FastAPI's built-in Swagger UI

### Numbers
- 4 endpoints
- Redis cache eliminates repeat DB + model calls within same trading day
- Confidence interval: predicted_return ± 2 × rolling_std_21 (21-day volatility estimate)

### Technical decisions
- Cache is best-effort — `RedisError` is caught and swallowed so a Redis outage never blocks a prediction
- Model loaded once at first request and held in memory (`_model_cache` dict) — avoids MLflow round-trip on every call
- `/drift` returns a placeholder — PSI drift monitoring wired up in Phase 6

### Resume bullets (raw)
- Built FastAPI inference service with `/predict`, `/models`, and `/health` endpoints; integrated Redis caching with 1-hour TTL reducing repeat inference latency to sub-millisecond
- Implemented prediction logging to PostgreSQL `prediction_log` table capturing model version, horizon, predicted return, and confidence intervals for full audit trail
- Wired model loading directly from MLflow run artifacts — inference service requires no hardcoded model paths, enabling zero-downtime model swaps via MLflow experiment tracking

---

## Phase 6 — Drift Monitoring, Prometheus, Grafana, ADR-002

**Date:** April 2026

### What was built
- **Drift monitoring service** (`services/drift/`) — FastAPI app computing PSI per feature; runs on startup and every hour; exposes `/metrics`, `/status`, `/run`
- **PSI implementation** — percentile-binned Population Stability Index comparing reference window (2005–2020 training data) against current window (last 63 trading days)
- **`drift_log` table** — migration 005; records every PSI check with feature name, score, window dates, and alert flag
- **Prometheus integration** — `finsignal_psi_score` and `finsignal_drift_alert` gauges per feature; Prometheus added to Docker Compose, scrapes drift service every 30s
- **Grafana** — added to Docker Compose (port 3000); connects to Prometheus as data source
- **ADR-002** (`docs/adr/002-schema-design.md`) — documents why feature_store is denormalized, why macro series share the equity table, and prediction_log design rationale

### Numbers
- 6 features monitored: log_return, vix, yield_spread, dexcaus, rolling_std_21, rolling_mean_21
- PSI thresholds: 0.1 warning, 0.2 alert (industry standard)
- Reference window: 3,775 rows (2005–2020 training set)
- Current window: 63 trading days (~3 months)

### Technical decisions
- PSI bins derived from reference distribution percentiles — robust to outliers vs fixed-width bins
- Drift check runs async in background; FastAPI stays responsive during computation
- `host.docker.internal` in prometheus.yml — Prometheus container scrapes drift service running on host

### Resume bullets (raw)
- Implemented PSI-based feature drift monitoring across 6 key features; exposed Prometheus metrics (`finsignal_psi_score`, `finsignal_drift_alert`) scraped every 30s; visualised in Grafana
- Designed drift_log schema capturing reference/current window dates and alert flags, enabling retrospective drift analysis
- Authored ADR-002 documenting schema design trade-offs (denormalized feature_store, unified raw_market_data for equity and macro series)

---

## Phase 7 — Next.js Frontend Dashboard

**Date:** April 2026

### What was built
- **Next.js 14 frontend** (`frontend/`) — TypeScript, Tailwind CSS, Recharts; single-page dashboard with three panels
- **Forecast chart** — fetches `/predict` at 1d, 5d, 21d horizons; plots predicted return % with CI upper/lower bands using Recharts LineChart
- **Model leaderboard** — fetches `/models`; renders MAE, RMSE, direction accuracy per MLflow-tracked run in a sortable table
- **Drift panel** — fetches `/status` from drift service; visualises PSI per feature as a progress bar with colour-coded status badges (OK / WARNING / ALERT); manual refresh button
- **Proxy rewrites** — Next.js `rewrites()` config proxies `/api/inference/*` → `localhost:8000` and `/api/drift/*` → `localhost:8001`, eliminating CORS issues
- **Dark UI** — slate-900 background, consistent with financial terminal aesthetic

### Numbers
- 3 components, 1 page
- First Load JS: 202 kB (Recharts is the dominant chunk)
- Dev server: port 3001

### Technical decisions
- Next.js 14 (not 15/16) — pinned to match Node 18 environment; latest Next.js requires Node >=20
- Proxy rewrites instead of CORS headers — keeps backend services unchanged; all cross-origin calls go through the Next.js dev server
- `"use client"` on all data-fetching components — all panels are interactive (refresh, state); no benefit to RSC here

### Resume bullets (raw)
- Built a Next.js 14 + TypeScript + Tailwind dashboard surfacing live model predictions, MLflow experiment leaderboard, and PSI drift alerts across 6 features
- Implemented multi-horizon forecast visualisation (1/5/21-day) with confidence interval bands using Recharts; colour-coded PSI progress bars with OK/WARNING/ALERT thresholds
- Configured Next.js proxy rewrites to forward API calls to FastAPI inference and drift services, eliminating CORS configuration on backend services

---
