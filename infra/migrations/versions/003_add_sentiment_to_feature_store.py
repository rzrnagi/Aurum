"""add sentiment_score to feature_store

Revision ID: 003
Revises: 002
Create Date: 2026-04-14
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "feature_store",
        sa.Column("sentiment_score", sa.Numeric(6, 4), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("feature_store", "sentiment_score")
