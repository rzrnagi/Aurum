import pandas as pd
from config import TRAIN_START, TRAIN_END, VAL_END, FEATURE_COLS


def make_splits(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split feature_store into train / val / test.
    Target is next-day log return: features at T predict log_return at T+1.
    """
    df = df.copy().sort_values("date").reset_index(drop=True)

    # Next-day log return as prediction target
    df["target"] = df["log_return"].shift(-1)

    # Drop last row (no target) and any remaining NaNs in features or target
    df = df.dropna(subset=FEATURE_COLS + ["target"])

    train = df[(df["date"] >= TRAIN_START) & (df["date"] < TRAIN_END)].copy()
    val = df[(df["date"] >= TRAIN_END) & (df["date"] < VAL_END)].copy()
    test = df[df["date"] >= VAL_END].copy()

    return train, val, test
