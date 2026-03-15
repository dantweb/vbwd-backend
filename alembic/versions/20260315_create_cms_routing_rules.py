"""create cms_routing_rules table

Revision ID: 20260315_cms_routing
Revises: g3h4i5j6k7l8
Create Date: 2026-03-15
"""
from alembic import op
import sqlalchemy as sa

revision = "20260315_cms_routing"
down_revision = "g3h4i5j6k7l8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cms_routing_rules",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("match_type", sa.String(32), nullable=False),
        sa.Column("match_value", sa.String(255), nullable=True),
        sa.Column("target_slug", sa.String(255), nullable=False),
        sa.Column("redirect_code", sa.Integer(), nullable=False, server_default="302"),
        sa.Column("is_rewrite", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("layer", sa.String(16), nullable=False, server_default="middleware"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_cms_routing_rules_priority", "cms_routing_rules", ["priority"])
    op.create_index("ix_cms_routing_rules_layer", "cms_routing_rules", ["layer"])


def downgrade():
    op.drop_index("ix_cms_routing_rules_layer", "cms_routing_rules")
    op.drop_index("ix_cms_routing_rules_priority", "cms_routing_rules")
    op.drop_table("cms_routing_rules")
