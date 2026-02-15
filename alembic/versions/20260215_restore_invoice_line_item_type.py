"""Restore item_type column to invoice_line_item table.

Revision ID: 20260215_restore_item_type
Revises: 20260215_enum_uppercase
Create Date: 2026-02-15 10:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision: str = "20260215_restore_item_type"
down_revision: Union[str, None] = "20260215_enum_uppercase"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Upgrade: Restore item_type column to invoice_line_item table."""

    # Drop the enum type if it exists (from previous migration), then recreate it
    op.execute("DROP TYPE IF EXISTS lineitemtype CASCADE")

    # Create the lineitemtype enum
    op.execute("CREATE TYPE lineitemtype AS ENUM ('SUBSCRIPTION', 'TOKEN_BUNDLE', 'ADD_ON')")

    # Add item_type column to invoice_line_item table
    op.add_column(
        'invoice_line_item',
        sa.Column(
            'item_type',
            ENUM('SUBSCRIPTION', 'TOKEN_BUNDLE', 'ADD_ON', name='lineitemtype'),
            nullable=False,
            server_default='SUBSCRIPTION'
        )
    )


def downgrade():
    """Downgrade: Remove item_type column from invoice_line_item table."""

    # Remove the column
    op.drop_column('invoice_line_item', 'item_type')

    # Drop the enum type
    op.execute("DROP TYPE lineitemtype CASCADE")
