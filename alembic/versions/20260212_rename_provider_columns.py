"""Rename provider-specific columns to generic names.

stripe_customer_id      -> payment_customer_id
stripe_subscription_id  -> provider_subscription_id  (merged with paypal_subscription_id)
stripe_invoice_id       -> provider_session_id        (merged with paypal_order_id)
addon stripe_sub_id     -> provider_subscription_id

Revision ID: 20260212_rename
Revises: 20260212_paypal
Create Date: 2026-02-12
"""
from alembic import op

revision = "20260212_rename"
down_revision = "20260212_paypal"
branch_labels = None
depends_on = None


def upgrade():
    # ---- user: stripe_customer_id -> payment_customer_id ----
    op.alter_column("user", "stripe_customer_id", new_column_name="payment_customer_id")

    # ---- subscription: merge stripe + paypal into provider_subscription_id ----
    # Copy paypal values into stripe column (they are mutually exclusive)
    op.execute(
        "UPDATE subscription SET stripe_subscription_id = paypal_subscription_id "
        "WHERE stripe_subscription_id IS NULL AND paypal_subscription_id IS NOT NULL"
    )
    op.drop_index("ix_subscription_paypal_subscription_id", table_name="subscription")
    op.drop_column("subscription", "paypal_subscription_id")
    op.alter_column(
        "subscription", "stripe_subscription_id", new_column_name="provider_subscription_id"
    )

    # ---- user_invoice: merge stripe + paypal into provider_session_id ----
    op.execute(
        "UPDATE user_invoice SET stripe_invoice_id = paypal_order_id "
        "WHERE stripe_invoice_id IS NULL AND paypal_order_id IS NOT NULL"
    )
    op.drop_index("ix_user_invoice_paypal_order_id", table_name="user_invoice")
    op.drop_column("user_invoice", "paypal_order_id")
    op.alter_column(
        "user_invoice", "stripe_invoice_id", new_column_name="provider_session_id"
    )

    # ---- addon_subscription: stripe_subscription_id -> provider_subscription_id ----
    op.alter_column(
        "addon_subscription", "stripe_subscription_id",
        new_column_name="provider_subscription_id",
    )


def downgrade():
    # ---- addon_subscription ----
    op.alter_column(
        "addon_subscription", "provider_subscription_id",
        new_column_name="stripe_subscription_id",
    )

    # ---- user_invoice: split back ----
    op.alter_column(
        "user_invoice", "provider_session_id", new_column_name="stripe_invoice_id"
    )
    op.add_column(
        "user_invoice",
        __import__("sqlalchemy").Column(
            "paypal_order_id", __import__("sqlalchemy").String(255),
            unique=True, nullable=True,
        ),
    )
    op.create_index(
        "ix_user_invoice_paypal_order_id", "user_invoice", ["paypal_order_id"]
    )

    # ---- subscription: split back ----
    op.alter_column(
        "subscription", "provider_subscription_id",
        new_column_name="stripe_subscription_id",
    )
    op.add_column(
        "subscription",
        __import__("sqlalchemy").Column(
            "paypal_subscription_id", __import__("sqlalchemy").String(255),
            unique=True, nullable=True,
        ),
    )
    op.create_index(
        "ix_subscription_paypal_subscription_id", "subscription",
        ["paypal_subscription_id"],
    )

    # ---- user ----
    op.alter_column("user", "payment_customer_id", new_column_name="stripe_customer_id")
