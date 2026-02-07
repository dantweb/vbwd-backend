"""add_payment_method_tables

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-01-22 14:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d4e5f6g7h8i9"
down_revision: Union[str, None] = "c3d4e5f6g7h8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create payment_method table
    op.create_table(
        "payment_method",
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("short_description", sa.String(length=255), nullable=True),
        sa.Column("icon", sa.String(length=255), nullable=True),
        sa.Column("plugin_id", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("min_amount", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("max_amount", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "currencies",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "countries",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "fee_type", sa.String(length=20), nullable=False, server_default="none"
        ),
        sa.Column("fee_amount", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column(
            "fee_charged_to",
            sa.String(length=20),
            nullable=False,
            server_default="customer",
        ),
        sa.Column(
            "config",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_payment_method_code"), "payment_method", ["code"], unique=True
    )
    op.create_index(
        op.f("ix_payment_method_is_active"),
        "payment_method",
        ["is_active"],
        unique=False,
    )

    # Create payment_method_translation table
    op.create_table(
        "payment_method_translation",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("payment_method_id", sa.UUID(), nullable=False),
        sa.Column("locale", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("short_description", sa.String(length=255), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["payment_method_id"], ["payment_method.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "payment_method_id", "locale", name="uq_payment_method_translation_locale"
        ),
    )
    op.create_index(
        op.f("ix_payment_method_translation_payment_method_id"),
        "payment_method_translation",
        ["payment_method_id"],
        unique=False,
    )

    # Seed default Invoice payment method
    op.execute(
        """
        INSERT INTO payment_method (code, name, description, short_description, is_active, is_default, position, fee_type, fee_charged_to)
        VALUES ('invoice', 'Invoice', 'Pay by invoice within 14 days', 'Pay by invoice', true, true, 0, 'none', 'customer')
    """
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_payment_method_translation_payment_method_id"),
        table_name="payment_method_translation",
    )
    op.drop_table("payment_method_translation")
    op.drop_index(op.f("ix_payment_method_is_active"), table_name="payment_method")
    op.drop_index(op.f("ix_payment_method_code"), table_name="payment_method")
    op.drop_table("payment_method")
