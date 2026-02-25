"""add_tarif_plan_category

Revision ID: m4n5o6p7q8r9
Revises: 23fc03c369f8
Create Date: 2026-02-25 10:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "m4n5o6p7q8r9"
down_revision: Union[str, None] = "23fc03c369f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed UUID for the root category
ROOT_CATEGORY_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    # Create tarif_plan_category table
    op.create_table(
        "tarif_plan_category",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "parent_id",
            sa.UUID(),
            sa.ForeignKey("tarif_plan_category.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "is_single", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "sort_order", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tarif_plan_category_slug"),
        "tarif_plan_category",
        ["slug"],
        unique=True,
    )
    op.create_index(
        op.f("ix_tarif_plan_category_parent_id"),
        "tarif_plan_category",
        ["parent_id"],
        unique=False,
    )

    # Create junction table
    op.create_table(
        "tarif_plan_category_plans",
        sa.Column(
            "category_id",
            sa.UUID(),
            sa.ForeignKey("tarif_plan_category.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tarif_plan_id",
            sa.UUID(),
            sa.ForeignKey("tarif_plan.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # Insert root category
    op.execute(
        f"""
        INSERT INTO tarif_plan_category (id, name, slug, description, parent_id, is_single, sort_order, created_at, updated_at, version)
        VALUES (
            '{ROOT_CATEGORY_ID}',
            'Root',
            'root',
            'Default root category',
            NULL,
            true,
            0,
            NOW(),
            NOW(),
            0
        )
        """
    )

    # Attach all existing plans to root category
    op.execute(
        f"""
        INSERT INTO tarif_plan_category_plans (category_id, tarif_plan_id)
        SELECT '{ROOT_CATEGORY_ID}', id FROM tarif_plan
        """
    )


def downgrade() -> None:
    op.drop_table("tarif_plan_category_plans")
    op.drop_index(
        op.f("ix_tarif_plan_category_parent_id"),
        table_name="tarif_plan_category",
    )
    op.drop_index(
        op.f("ix_tarif_plan_category_slug"),
        table_name="tarif_plan_category",
    )
    op.drop_table("tarif_plan_category")
