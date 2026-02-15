"""Create user token balance and token transaction tables.

Revision ID: 20260215_token_bal
Revises: 20260215_role_perm
Create Date: 2026-02-15 08:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM

# revision identifiers, used by Alembic.
revision: str = "20260215_token_bal"
down_revision: Union[str, None] = "20260215_role_perm"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user_token_balance and token_transaction tables."""
    # Create TokenTransactionType enum
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE tokentransactiontype AS ENUM ('purchase', 'usage', 'refund', 'bonus', 'adjustment'); "
        "EXCEPTION WHEN duplicate_object THEN null; "
        "END $$;"
    )

    # Create user_token_balance table
    op.create_table(
        "user_token_balance",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_token_balance_user_id"),
    )
    op.create_index("ix_user_token_balance_user_id", "user_token_balance", ["user_id"], unique=True)

    # Create token_transaction table
    tokentransactiontype_enum = ENUM(
        "purchase",
        "usage",
        "refund",
        "bonus",
        "adjustment",
        name="tokentransactiontype",
        create_type=False,
    )

    op.create_table(
        "token_transaction",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("transaction_type", tokentransactiontype_enum, nullable=False),
        sa.Column("reference_id", UUID(as_uuid=True), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_token_transaction_user_id", "token_transaction", ["user_id"], unique=False)
    op.create_index("ix_token_transaction_reference_id", "token_transaction", ["reference_id"], unique=False)


def downgrade() -> None:
    """Drop user_token_balance and token_transaction tables."""
    op.drop_index("ix_token_transaction_reference_id", table_name="token_transaction")
    op.drop_index("ix_token_transaction_user_id", table_name="token_transaction")
    op.drop_table("token_transaction")

    op.drop_index("ix_user_token_balance_user_id", table_name="user_token_balance")
    op.drop_table("user_token_balance")

    op.execute("DROP TYPE tokentransactiontype")
