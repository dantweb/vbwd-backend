"""Make tarif_plan_id nullable in user_invoice table.

Revision ID: 20260215_nullable_tarif_plan
Revises: 20260215_restore_item_type
Create Date: 2026-02-15 11:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260215_nullable_tarif_plan"
down_revision: Union[str, None] = "20260215_restore_item_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Upgrade: Make tarif_plan_id nullable to support invoices without plans."""

    # Alter the column to be nullable
    op.alter_column(
        "user_invoice",
        "tarif_plan_id",
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade():
    """Downgrade: Make tarif_plan_id not nullable."""

    op.alter_column(
        "user_invoice",
        "tarif_plan_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
