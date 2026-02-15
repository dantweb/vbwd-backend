"""Add missing subscription columns

Revision ID: h8i9j0k1l2m3
Revises: 20260212_rename
Create Date: 2026-02-14 16:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "h8i9j0k1l2m3"
down_revision: Union[str, None] = "20260212_rename"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pending_plan_id and paused_at columns to subscription table."""
    # Add pending_plan_id column
    op.add_column(
        "subscription",
        sa.Column("pending_plan_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_subscription_pending_plan_id_tarif_plan",
        "subscription",
        "tarif_plan",
        ["pending_plan_id"],
        ["id"],
    )

    # Add paused_at column
    op.add_column(
        "subscription",
        sa.Column("paused_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Remove pending_plan_id and paused_at columns from subscription table."""
    # Remove paused_at column
    op.drop_column("subscription", "paused_at")

    # Remove pending_plan_id column
    op.drop_constraint(
        "fk_subscription_pending_plan_id_tarif_plan",
        "subscription",
        type_="foreignkey",
    )
    op.drop_column("subscription", "pending_plan_id")
