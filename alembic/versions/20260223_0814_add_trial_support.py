"""add_trial_support

Revision ID: 23fc03c369f8
Revises: 9f128e1f428c
Create Date: 2026-02-23 08:14:40.369574+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23fc03c369f8'
down_revision: Union[str, None] = '9f128e1f428c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS 'TRIALING'")
    op.add_column('tarif_plan', sa.Column('trial_days', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('subscription', sa.Column('trial_end_at', sa.DateTime(), nullable=True))
    op.execute("ALTER TABLE \"user\" ADD COLUMN has_used_trial BOOLEAN NOT NULL DEFAULT false")


def downgrade() -> None:
    op.execute('ALTER TABLE "user" DROP COLUMN IF EXISTS has_used_trial')
    op.drop_column('subscription', 'trial_end_at')
    op.drop_column('tarif_plan', 'trial_days')
