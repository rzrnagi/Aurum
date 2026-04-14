# ADR-002: PostgreSQL Schema Design

**Date:** April 2026
**Status:** Accepted

---

## Context

FinSignal needs a PostgreSQL schema that supports: raw data ingestion, ML feature storage, inference logging, and drift monitoring. The design must be performant for time-series queries and explainable in a technical interview.

---

## Decision

Four tables, each with a single clear responsibility.

### `raw_market_data`
Immutable append-only log of everything ingested. Never updated — only inserted. Serves as the source of truth for reprocessing features from scratch.

**Key design choice:** FRED macro series (CAD/USD, yield spread) share the same table as equity OHLCV, with `open/high/low/volume` left NULL. Alternative was a separate `macro_data` table, but a unified schema simplifies the feature engineering join and reduces query complexity at no storage cost.

### `feature_store`
Denormalized: one wide row per (ticker, date) with all 28 engineered features pre-computed. Deliberately not normalized into separate `lag_features`, `rolling_features`, `macro_features` tables.

**Why denormalized:** The training and inference queries always need all features together. Normalizing would require a multi-table join on every model call, adding latency with no benefit — the feature matrix is always consumed as a unit, never queried by individual feature type.

### `prediction_log`
Append-only record of every inference call. Stores model name, version (MLflow run ID prefix), predicted return, confidence bounds, and horizon. Enables:
- Auditability: reconstruct what the model predicted on any date
- Backtesting: compare predicted vs actual returns after the fact
- Drift detection: compare prediction distribution over time

### `drift_log`
One row per PSI check per feature. Stores the reference and current window dates alongside the PSI score and alert flag. Separating drift events from prediction events keeps both tables queryable independently and avoids NULL columns.

---

## Consequences

- Feature store rows must be recomputed when raw data is revised (no lazy recomputation)
- `prediction_log` grows by ~4 rows/day (one per horizon) — negligible storage
- Schema changes require Alembic migrations — all 5 migrations are versioned and reversible via `alembic downgrade`
