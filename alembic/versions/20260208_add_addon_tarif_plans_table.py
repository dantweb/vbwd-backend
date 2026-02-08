"""add_addon_tarif_plans_junction_table

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j1
Create Date: 2026-02-08 14:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f6g7h8i9j0k1"
down_revision: Union[str, None] = "e5f6g7h8i9j1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "addon_tarif_plans",
        sa.Column("addon_id", sa.UUID(), nullable=False),
        sa.Column("tarif_plan_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["addon_id"], ["addon.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tarif_plan_id"], ["tarif_plan.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("addon_id", "tarif_plan_id"),
    )
    op.create_index(
        "ix_addon_tarif_plans_plan",
        "addon_tarif_plans",
        ["tarif_plan_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_addon_tarif_plans_plan", table_name="addon_tarif_plans")
    op.drop_table("addon_tarif_plans")
