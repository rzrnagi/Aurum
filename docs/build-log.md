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
