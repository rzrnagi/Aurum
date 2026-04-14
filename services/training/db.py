import pandas as pd
from sqlalchemy import create_engine, text
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)


def load_feature_store(ticker: str = "GSPC") -> pd.DataFrame:
    query = text(
        "SELECT * FROM feature_store WHERE ticker = :ticker ORDER BY date"
    )
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"ticker": ticker})
    df["date"] = pd.to_datetime(df["date"])
    return df
