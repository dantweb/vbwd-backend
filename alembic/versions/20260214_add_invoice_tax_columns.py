"""Add invoice tax columns

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-02-14 16:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "i9j0k1l2m3n4"
down_revision: Union[str, None] = "h8i9j0k1l2m3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add subtotal, tax_amount, and total_amount columns to user_invoice table."""
    # Add subtotal column
    op.add_column(
        "user_invoice",
        sa.Column("subtotal", sa.Numeric(precision=10, scale=2), nullable=True),
    )

    # Add tax_amount column
    op.add_column(
        "user_invoice",
        sa.Column(
            "tax_amount",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
            server_default="0",
        ),
    )

    # Add total_amount column
    op.add_column(
        "user_invoice",
        sa.Column("total_amount", sa.Numeric(precision=10, scale=2), nullable=True),
    )

    # Migrate existing data: copy amount to subtotal and total_amount
    op.execute(
        """
        UPDATE user_invoice
        SET subtotal = amount,
            total_amount = amount,
            tax_amount = 0
        WHERE subtotal IS NULL
        """
    )


def downgrade() -> None:
    """Remove subtotal, tax_amount, and total_amount columns from user_invoice table."""
    op.drop_column("user_invoice", "total_amount")
    op.drop_column("user_invoice", "tax_amount")
    op.drop_column("user_invoice", "subtotal")
