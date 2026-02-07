"""add_addon_table

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-01-13 11:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create addon table
    op.create_table(
        "addon",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "price",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "currency", sa.String(length=3), nullable=False, server_default="EUR"
        ),
        sa.Column(
            "billing_period",
            sa.String(length=50),
            nullable=False,
            server_default="monthly",
        ),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_addon_is_active"), "addon", ["is_active"], unique=False)
    op.create_index(op.f("ix_addon_slug"), "addon", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_addon_slug"), table_name="addon")
    op.drop_index(op.f("ix_addon_is_active"), table_name="addon")
    op.drop_table("addon")
