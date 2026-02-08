"""add_plugin_config_table

Revision ID: e5f6g7h8i9j1
Revises: e5f6g7h8i9j0
Create Date: 2026-02-07 10:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e5f6g7h8i9j1"
down_revision: Union[str, None] = "e5f6g7h8i9j0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "plugin_config",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("plugin_name", sa.String(length=100), nullable=False),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="disabled"
        ),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column("enabled_at", sa.DateTime(), nullable=True),
        sa.Column("disabled_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_plugin_config_plugin_name"),
        "plugin_config",
        ["plugin_name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_plugin_config_plugin_name"), table_name="plugin_config")
    op.drop_table("plugin_config")
