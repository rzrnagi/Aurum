"""create feature_store table

Revision ID: 002
Revises: 001
Create Date: 2026-04-14
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LAG_COLS = [sa.Column(f"lag_{i}", sa.Numeric(10, 6)) for i in range(1, 21)]


def upgrade() -> None:
    op.create_table(
        "feature_store",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("log_return", sa.Numeric(10, 6)),
        *LAG_COLS,
        sa.Column("rolling_mean_5", sa.Numeric(10, 6)),
        sa.Column("rolling_mean_21", sa.Numeric(10, 6)),
        sa.Column("rolling_std_5", sa.Numeric(10, 6)),
        sa.Column("rolling_std_21", sa.Numeric(10, 6)),
        sa.Column("vix", sa.Numeric(10, 4)),
        sa.Column("dexcaus", sa.Numeric(10, 6)),
        sa.Column("yield_spread", sa.Numeric(10, 6)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("ticker", "date", name="uq_feature_ticker_date"),
    )
    op.create_index(
        "idx_feature_store_ticker_date",
        "feature_store",
        ["ticker", "date"],
    )


def downgrade() -> None:
    op.drop_index("idx_feature_store_ticker_date", table_name="feature_store")
    op.drop_table("feature_store")
