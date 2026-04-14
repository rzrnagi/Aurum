import logging
from sqlalchemy.dialects.postgresql import insert
from db import engine, feature_store
from engineer import compute_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def upsert_features(df) -> int:
    records = df.to_dict(orient="records")
    with engine.begin() as conn:
        result = conn.execute(
            insert(feature_store)
            .values(records)
            .on_conflict_do_update(
                index_elements=["ticker", "date"],
                set_={
                    col: insert(feature_store).excluded[col]
                    for col in df.columns
                    if col not in ("ticker", "date")
                },
            )
        )
    return result.rowcount


def main() -> None:
    log.info("Computing features...")
    df = compute_features()
    log.info(f"Feature matrix: {len(df)} rows × {len(df.columns)} columns")

    upserted = upsert_features(df)
    log.info(f"Upserted {upserted} rows into feature_store")


if __name__ == "__main__":
    main()
