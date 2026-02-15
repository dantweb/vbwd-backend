"""Create feature usage table.

Revision ID: 20260215_feature_usage
Revises: 20260215_password_reset
Create Date: 2026-02-15 09:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "20260215_feature_usage"
down_revision: Union[str, None] = "20260215_password_reset"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create feature_usage table."""
    op.create_table(
        "feature_usage",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("feature_name", sa.String(length=100), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "feature_name", "period_start", name="uq_user_feature_period"
        ),
    )
    op.create_index("ix_feature_usage_user_id", "feature_usage", ["user_id"], unique=False)
    op.create_index("ix_feature_usage_feature_name", "feature_usage", ["feature_name"], unique=False)
    op.create_index("ix_feature_usage_period_start", "feature_usage", ["period_start"], unique=False)


def downgrade() -> None:
    """Drop feature_usage table."""
    op.drop_index("ix_feature_usage_period_start", table_name="feature_usage")
    op.drop_index("ix_feature_usage_feature_name", table_name="feature_usage")
    op.drop_index("ix_feature_usage_user_id", table_name="feature_usage")
    op.drop_table("feature_usage")
