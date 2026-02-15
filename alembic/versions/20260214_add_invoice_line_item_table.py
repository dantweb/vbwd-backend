"""Add invoice_line_item table

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-02-14 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM

# revision identifiers, used by Alembic.
revision: str = "j0k1l2m3n4o5"
down_revision: Union[str, None] = "i9j0k1l2m3n4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create invoice_line_item table."""
    # Create LineItemType enum if it doesn't exist
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE lineitemtype AS ENUM ('subscription', 'token_bundle', 'add_on'); "
        "EXCEPTION WHEN duplicate_object THEN null; "
        "END $$;"
    )

    # Create invoice_line_item table
    # Use ENUM type with create_type=False to avoid trying to create the type again
    lineitemtype_enum = ENUM(
        "subscription",
        "token_bundle",
        "add_on",
        name="lineitemtype",
        create_type=False,
    )

    op.create_table(
        "invoice_line_item",
        sa.Column("invoice_id", UUID(as_uuid=True), nullable=False),
        sa.Column("item_type", lineitemtype_enum, nullable=False),
        sa.Column("item_id", UUID(as_uuid=True), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("total_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["invoice_id"], ["user_invoice.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        op.f("ix_invoice_line_item_invoice_id"),
        "invoice_line_item",
        ["invoice_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_invoice_line_item_item_id"),
        "invoice_line_item",
        ["item_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop invoice_line_item table."""
    op.drop_index(
        op.f("ix_invoice_line_item_item_id"), table_name="invoice_line_item"
    )
    op.drop_index(
        op.f("ix_invoice_line_item_invoice_id"), table_name="invoice_line_item"
    )
    op.drop_table("invoice_line_item")
    op.execute("DROP TYPE lineitemtype")
