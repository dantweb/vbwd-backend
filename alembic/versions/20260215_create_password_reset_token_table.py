"""Create password reset token table.

Revision ID: 20260215_password_reset
Revises: 20260215_token_bal
Create Date: 2026-02-15 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "20260215_password_reset"
down_revision: Union[str, None] = "20260215_token_bal"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create password_reset_token table."""
    op.create_table(
        "password_reset_token",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_password_reset_token_token"),
    )
    op.create_index("ix_password_reset_token_user_id", "password_reset_token", ["user_id"], unique=False)
    op.create_index("ix_password_reset_token_token", "password_reset_token", ["token"], unique=True)


def downgrade() -> None:
    """Drop password_reset_token table."""
    op.drop_index("ix_password_reset_token_token", table_name="password_reset_token")
    op.drop_index("ix_password_reset_token_user_id", table_name="password_reset_token")
    op.drop_table("password_reset_token")
