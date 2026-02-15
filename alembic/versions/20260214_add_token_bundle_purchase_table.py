"""Add token_bundle_purchase table

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-02-14 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM

# revision identifiers, used by Alembic.
revision: str = "k1l2m3n4o5p6"
down_revision: Union[str, None] = "j0k1l2m3n4o5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create token_bundle_purchase table."""
    # Create PurchaseStatus enum if it doesn't exist
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE purchasestatus AS ENUM ('pending', 'completed', 'refunded', 'cancelled'); "
        "EXCEPTION WHEN duplicate_object THEN null; "
        "END $$;"
    )

    # Create token_bundle_purchase table
    purchasestatus_enum = ENUM(
        "pending",
        "completed",
        "refunded",
        "cancelled",
        name="purchasestatus",
        create_type=False,
    )

    op.create_table(
        "token_bundle_purchase",
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("bundle_id", UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", purchasestatus_enum, nullable=False),
        sa.Column("tokens_credited", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("token_amount", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bundle_id"], ["token_bundle.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["user_invoice.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        op.f("ix_token_bundle_purchase_user_id"),
        "token_bundle_purchase",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_token_bundle_purchase_bundle_id"),
        "token_bundle_purchase",
        ["bundle_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_token_bundle_purchase_invoice_id"),
        "token_bundle_purchase",
        ["invoice_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_token_bundle_purchase_status"),
        "token_bundle_purchase",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Drop token_bundle_purchase table."""
    op.drop_index(
        op.f("ix_token_bundle_purchase_status"), table_name="token_bundle_purchase"
    )
    op.drop_index(
        op.f("ix_token_bundle_purchase_invoice_id"), table_name="token_bundle_purchase"
    )
    op.drop_index(
        op.f("ix_token_bundle_purchase_bundle_id"), table_name="token_bundle_purchase"
    )
    op.drop_index(
        op.f("ix_token_bundle_purchase_user_id"), table_name="token_bundle_purchase"
    )
    op.drop_table("token_bundle_purchase")
    op.execute("DROP TYPE purchasestatus")
