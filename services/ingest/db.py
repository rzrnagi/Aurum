from sqlalchemy import (
    BigInteger, Column, create_engine, Date, DateTime,
    Index, Integer, MetaData, Numeric, String, Table, UniqueConstraint,
    func, select,
)
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
metadata = MetaData()

raw_market_data = Table(
    "raw_market_data",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("ticker", String(20), nullable=False),
    Column("date", Date, nullable=False),
    Column("open", Numeric(12, 4)),
    Column("high", Numeric(12, 4)),
    Column("low", Numeric(12, 4)),
    Column("close", Numeric(12, 4)),
    Column("volume", BigInteger),
    Column("ingested_at", DateTime(timezone=True), server_default=func.now()),
    UniqueConstraint("ticker", "date", name="uq_ticker_date"),
)

Index("idx_raw_market_data_ticker_date", raw_market_data.c.ticker, raw_market_data.c.date)


def get_last_date(ticker: str):
    """Return the most recently ingested date for a ticker, or None."""
    with engine.connect() as conn:
        return conn.execute(
            select(func.max(raw_market_data.c.date)).where(
                raw_market_data.c.ticker == ticker
            )
        ).scalar()
