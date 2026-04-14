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
