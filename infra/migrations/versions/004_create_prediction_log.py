"""create prediction_log table

Revision ID: 004
Revises: 003
Create Date: 2026-04-14
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prediction_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_name", sa.String(50), nullable=False),
        sa.Column("model_version", sa.String(50)),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column("predicted_return", sa.Numeric(10, 6)),
        sa.Column("confidence_lower", sa.Numeric(10, 6)),
        sa.Column("confidence_upper", sa.Numeric(10, 6)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "idx_prediction_log_ticker_date",
        "prediction_log",
        ["ticker", "forecast_date", "horizon_days"],
    )


def downgrade() -> None:
    op.drop_index("idx_prediction_log_ticker_date", table_name="prediction_log")
    op.drop_table("prediction_log")
