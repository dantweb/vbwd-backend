"""Create addon subscription table.

Revision ID: 20260215_addon_subscription
Revises: 20260215_feature_usage
Create Date: 2026-02-15 09:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM

# revision identifiers, used by Alembic.
revision: str = "20260215_addon_subscription"
down_revision: Union[str, None] = "20260215_feature_usage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create addon_subscription table."""
    # Use existing subscriptionstatus enum (created by subscription table)
    subscriptionstatus_enum = ENUM(
        "pending",
        "active",
        "expired",
        "cancelled",
        name="subscriptionstatus",
        create_type=False,
    )

    op.create_table(
        "addon_subscription",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("addon_id", UUID(as_uuid=True), nullable=False),
        sa.Column("subscription_id", UUID(as_uuid=True), nullable=True),
        sa.Column("invoice_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", subscriptionstatus_enum, nullable=False),
        sa.Column("starts_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("provider_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["addon_id"], ["addon.id"]),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscription.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["user_invoice.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_addon_subscription_user_id", "addon_subscription", ["user_id"], unique=False)
    op.create_index("ix_addon_subscription_addon_id", "addon_subscription", ["addon_id"], unique=False)
    op.create_index("ix_addon_subscription_subscription_id", "addon_subscription", ["subscription_id"], unique=False)
    op.create_index("ix_addon_subscription_invoice_id", "addon_subscription", ["invoice_id"], unique=False)
    op.create_index("ix_addon_subscription_status", "addon_subscription", ["status"], unique=False)
    op.create_index("ix_addon_subscription_expires_at", "addon_subscription", ["expires_at"], unique=False)
    op.create_index("ix_addon_subscription_provider_subscription_id", "addon_subscription", ["provider_subscription_id"], unique=False)


def downgrade() -> None:
    """Drop addon_subscription table."""
    op.drop_index("ix_addon_subscription_provider_subscription_id", table_name="addon_subscription")
    op.drop_index("ix_addon_subscription_expires_at", table_name="addon_subscription")
    op.drop_index("ix_addon_subscription_status", table_name="addon_subscription")
    op.drop_index("ix_addon_subscription_invoice_id", table_name="addon_subscription")
    op.drop_index("ix_addon_subscription_subscription_id", table_name="addon_subscription")
    op.drop_index("ix_addon_subscription_addon_id", table_name="addon_subscription")
    op.drop_index("ix_addon_subscription_user_id", table_name="addon_subscription")
    op.drop_table("addon_subscription")
