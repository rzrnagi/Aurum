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

### Architecture decisions
- TFT hidden_size=32, 2 attention heads — intentionally small for CPU training; GPU would scale to hidden_size=128+
- Sentiment stored in feature_store, not a separate table — keeps training queries simple; one join instead of two
- Finnhub free tier provides ~1-2 years of historical headlines; NULL sentinel on older dates; LightGBM+Sentiment trains only on non-null rows
- LSTM explicitly excluded (ADR-001) — TFT strictly dominates, showing deliberate engineering judgment

### Resume bullets (raw)
- Implemented Temporal Fusion Transformer for multi-horizon (1/5/21-day) S&P 500 return forecasting using pytorch-forecasting; logged attention weight interpretation plots to MLflow demonstrating model interpretability
- Built end-to-end sentiment pipeline: Finnhub API news ingestion → FinBERT (`ProsusAI/finbert`) confidence-weighted scoring → PostgreSQL feature store; integrated as engineered feature in LightGBM ablation study
- Authored ADR-001 documenting model selection rationale (TFT over LSTM, ARIMA as baseline), demonstrating engineering decision-making aligned with production ML standards

---
