"""Add PayPal fields to subscription and invoice models.

Revision ID: 20260212_paypal
Revises: 20260211_stripe_customer
Create Date: 2026-02-12
"""
import sqlalchemy as sa
from alembic import op

revision = "20260212_paypal"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "subscription",
        sa.Column("paypal_subscription_id", sa.String(255), unique=True, nullable=True),
    )
    op.create_index(
        "ix_subscription_paypal_subscription_id",
        "subscription",
        ["paypal_subscription_id"],
    )

    op.add_column(
        "user_invoice",
        sa.Column("paypal_order_id", sa.String(255), unique=True, nullable=True),
    )
    op.create_index(
        "ix_user_invoice_paypal_order_id",
        "user_invoice",
        ["paypal_order_id"],
    )


def downgrade():
    op.drop_index("ix_user_invoice_paypal_order_id", table_name="user_invoice")
    op.drop_column("user_invoice", "paypal_order_id")
    op.drop_index("ix_subscription_paypal_subscription_id", table_name="subscription")
    op.drop_column("subscription", "paypal_subscription_id")
