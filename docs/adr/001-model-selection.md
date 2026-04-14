# ADR-001: Model Selection for Financial Time Series Forecasting

**Date:** April 2026
**Status:** Accepted

---

## Context

FinSignal needs to forecast S&P 500 log returns across three horizons (1-day, 5-day, 21-day). The model selection must demonstrate both financial domain fluency and ML engineering depth for the RBC Borealis role evaluation.

Four candidate model types were considered.

---

## Options Considered

### 1. ARIMA
- **Pros:** Interpretable, well-understood in finance, fast to train, natural baseline
- **Cons:** Linear, no exogenous feature support in base form, assumes stationarity
- **Role:** Baseline — establishes the floor any ML model must beat

### 2. LightGBM with lag features
- **Pros:** Handles tabular features well, fast training, interpretable via feature importance, handles non-linear interactions
- **Cons:** No native sequence modelling, requires manual feature engineering
- **Role:** Core model — best risk-adjusted choice for daily return prediction

### 3. LSTM
- **Pros:** Sequence-native, widely used
- **Cons:** Slower to train than TFT, less interpretable, no built-in multi-horizon support, largely superseded by attention-based models
- **Decision:** Excluded — TFT strictly dominates LSTM for this use case

### 4. Temporal Fusion Transformer (TFT)
- **Pros:** Multi-horizon by design, handles mixed known/unknown covariates, attention-based interpretability (variable importance, attention weights), state-of-the-art on benchmark time series datasets
- **Cons:** Heavier to train (requires PyTorch), more complex setup, needs longer sequences
- **Role:** Advanced model — demonstrates PyTorch depth and multi-horizon capability

---

## Decision

Deploy all three (ARIMA, LightGBM, TFT). Exclude LSTM.

- ARIMA serves as the statistical baseline
- LightGBM is the production-grade daily inference model (fast, interpretable, <200ms p95)
- TFT handles 5-day and 21-day horizon forecasts where sequence modelling adds value

---

## Consequences

- Training service must support three model types with a shared evaluation interface
- MLflow tracks all runs under the `finsignal` experiment for side-by-side comparison
- LightGBM feature importance and TFT attention weights both feed the ablation narrative
- LSTM exclusion is a deliberate engineering decision, not an omission — worth stating in interviews
