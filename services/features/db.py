from sqlalchemy import (
    BigInteger, Column, create_engine, Date, DateTime,
    Index, Integer, MetaData, Numeric, String, Table, UniqueConstraint,
    func, select,
)
from config import DATABASE_URL, N_LAGS

engine = create_engine(DATABASE_URL)
metadata = MetaData()

raw_market_data = Table(
    "raw_market_data",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("ticker", String(20)),
    Column("date", Date),
    Column("close", Numeric(12, 4)),
    Column("volume", BigInteger),
)

_lag_cols = [Column(f"lag_{i}", Numeric(10, 6)) for i in range(1, N_LAGS + 1)]

feature_store = Table(
    "feature_store",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("ticker", String(20), nullable=False),
    Column("date", Date, nullable=False),
    Column("log_return", Numeric(10, 6)),
    *_lag_cols,
    Column("rolling_mean_5", Numeric(10, 6)),
    Column("rolling_mean_21", Numeric(10, 6)),
    Column("rolling_std_5", Numeric(10, 6)),
    Column("rolling_std_21", Numeric(10, 6)),
    Column("vix", Numeric(10, 4)),
    Column("dexcaus", Numeric(10, 6)),
    Column("yield_spread", Numeric(10, 6)),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    UniqueConstraint("ticker", "date", name="uq_feature_ticker_date"),
)

Index("idx_feature_store_ticker_date", feature_store.c.ticker, feature_store.c.date)


def load_series(ticker: str) -> list[tuple]:
    """Return (date, close) rows for a ticker, ordered by date."""
    with engine.connect() as conn:
        return conn.execute(
            select(raw_market_data.c.date, raw_market_data.c.close)
            .where(raw_market_data.c.ticker == ticker)
            .order_by(raw_market_data.c.date)
        ).fetchall()
