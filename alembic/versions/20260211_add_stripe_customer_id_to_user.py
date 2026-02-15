"""add_stripe_columns

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2026-02-11 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "g7h8i9j0k1l2"
down_revision: Union[str, None] = "f6g7h8i9j0k1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # user.stripe_customer_id
    op.add_column(
        "user",
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint(
        "uq_user_stripe_customer_id", "user", ["stripe_customer_id"]
    )
    op.create_index(
        "ix_user_stripe_customer_id", "user", ["stripe_customer_id"]
    )

    # subscription.stripe_subscription_id
    op.add_column(
        "subscription",
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint(
        "uq_subscription_stripe_subscription_id", "subscription", ["stripe_subscription_id"]
    )
    op.create_index(
        "ix_subscription_stripe_subscription_id", "subscription", ["stripe_subscription_id"]
    )

    # user_invoice.stripe_invoice_id
    op.add_column(
        "user_invoice",
        sa.Column("stripe_invoice_id", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint(
        "uq_user_invoice_stripe_invoice_id", "user_invoice", ["stripe_invoice_id"]
    )
    op.create_index(
        "ix_user_invoice_stripe_invoice_id", "user_invoice", ["stripe_invoice_id"]
    )

    # addon_subscription.stripe_subscription_id
    # NOTE: Commented out because addon_subscription table is created in 20260215_addon_subscription
    # op.add_column(
    #     "addon_subscription",
    #     sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
    # )
    # op.create_index(
    #     "ix_addon_subscription_stripe_subscription_id", "addon_subscription", ["stripe_subscription_id"]
    # )


def downgrade() -> None:
    # addon_subscription
    # NOTE: Commented out because addon_subscription table doesn't exist yet
    # op.drop_index("ix_addon_subscription_stripe_subscription_id", table_name="addon_subscription")
    # op.drop_column("addon_subscription", "stripe_subscription_id")

    # user_invoice
    op.drop_index("ix_user_invoice_stripe_invoice_id", table_name="user_invoice")
    op.drop_constraint("uq_user_invoice_stripe_invoice_id", "user_invoice", type_="unique")
    op.drop_column("user_invoice", "stripe_invoice_id")

    # subscription
    op.drop_index("ix_subscription_stripe_subscription_id", table_name="subscription")
    op.drop_constraint("uq_subscription_stripe_subscription_id", "subscription", type_="unique")
    op.drop_column("subscription", "stripe_subscription_id")

    # user
    op.drop_index("ix_user_stripe_customer_id", table_name="user")
    op.drop_constraint("uq_user_stripe_customer_id", "user", type_="unique")
    op.drop_column("user", "stripe_customer_id")
