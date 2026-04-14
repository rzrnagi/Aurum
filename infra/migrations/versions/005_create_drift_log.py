"""create drift_log table

Revision ID: 005
Revises: 004
Create Date: 2026-04-14
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "drift_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("feature_name", sa.String(50), nullable=False),
        sa.Column("psi_score", sa.Numeric(8, 6), nullable=False),
        sa.Column("reference_window_start", sa.Date(), nullable=False),
        sa.Column("reference_window_end", sa.Date(), nullable=False),
        sa.Column("current_window_start", sa.Date(), nullable=False),
        sa.Column("current_window_end", sa.Date(), nullable=False),
        sa.Column("alert_triggered", sa.Boolean(), default=False),
        sa.Column("detection_time", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_drift_log_feature_time", "drift_log", ["feature_name", "detection_time"])


def downgrade() -> None:
    op.drop_index("idx_drift_log_feature_time", table_name="drift_log")
    op.drop_table("drift_log")
