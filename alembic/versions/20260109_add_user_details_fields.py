"""add_company_tax_config_balance_to_user_details

Revision ID: a1b2c3d4e5f6
Revises: e3bb91853ab7
Create Date: 2026-01-09 10:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'e3bb91853ab7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to user_details table
    op.add_column('user_details', sa.Column('company', sa.String(length=255), nullable=True))
    op.add_column('user_details', sa.Column('tax_number', sa.String(length=100), nullable=True))
    op.add_column('user_details', sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('user_details', sa.Column('balance', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'))


def downgrade() -> None:
    # Remove added columns
    op.drop_column('user_details', 'balance')
    op.drop_column('user_details', 'config')
    op.drop_column('user_details', 'tax_number')
    op.drop_column('user_details', 'company')
