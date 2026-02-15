"""Update enum values to uppercase for consistency.

Revision ID: 20260215_enum_uppercase
Revises: 20260215_addon_subscription
Create Date: 2026-02-15 10:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260215_enum_uppercase"
down_revision: Union[str, None] = "20260215_addon_subscription"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Upgrade: Convert enum values from lowercase to UPPERCASE for PurchaseStatus and TokenTransactionType."""

    # Update PurchaseStatus enum
    # First rename the old type
    op.execute("ALTER TYPE purchasestatus RENAME TO purchasestatus_old")

    # Create new enum type with uppercase values
    op.execute("CREATE TYPE purchasestatus AS ENUM ('PENDING', 'COMPLETED', 'REFUNDED', 'CANCELLED')")

    # Convert existing data in token_bundle_purchase table
    op.execute("""
        ALTER TABLE token_bundle_purchase
        ALTER COLUMN status TYPE purchasestatus
        USING (upper(status::text))::purchasestatus
    """)

    # Drop old enum type
    op.execute("DROP TYPE purchasestatus_old")

    # Update TokenTransactionType enum
    op.execute("ALTER TYPE tokentransactiontype RENAME TO tokentransactiontype_old")
    op.execute("CREATE TYPE tokentransactiontype AS ENUM ('PURCHASE', 'USAGE', 'REFUND', 'BONUS', 'ADJUSTMENT')")

    op.execute("""
        ALTER TABLE token_transaction
        ALTER COLUMN transaction_type TYPE tokentransactiontype
        USING (upper(transaction_type::text))::tokentransactiontype
    """)

    op.execute("DROP TYPE tokentransactiontype_old")


def downgrade():
    """Downgrade: Convert enum values back to lowercase."""

    # Revert PurchaseStatus enum
    op.execute("ALTER TYPE purchasestatus RENAME TO purchasestatus_new")
    op.execute("CREATE TYPE purchasestatus AS ENUM ('pending', 'completed', 'refunded', 'cancelled')")

    op.execute("""
        ALTER TABLE token_bundle_purchase
        ALTER COLUMN status TYPE purchasestatus
        USING (lower(status::text))::purchasestatus
    """)

    op.execute("DROP TYPE purchasestatus_new")

    # Revert TokenTransactionType enum
    op.execute("ALTER TYPE tokentransactiontype RENAME TO tokentransactiontype_new")
    op.execute("CREATE TYPE tokentransactiontype AS ENUM ('purchase', 'usage', 'refund', 'bonus', 'adjustment')")

    op.execute("""
        ALTER TABLE token_transaction
        ALTER COLUMN transaction_type TYPE tokentransactiontype
        USING (lower(transaction_type::text))::tokentransactiontype
    """)

    op.execute("DROP TYPE tokentransactiontype_new")
