"""add_country_table

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-01-22 16:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e5f6g7h8i9j0"
down_revision: Union[str, None] = "d4e5f6g7h8i9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Default countries list (ISO 3166-1 alpha-2)
DEFAULT_COUNTRIES = [
    ("DE", "Germany"),
    ("AT", "Austria"),
    ("CH", "Switzerland"),
    ("US", "United States"),
    ("GB", "United Kingdom"),
    ("FR", "France"),
    ("IT", "Italy"),
    ("ES", "Spain"),
    ("NL", "Netherlands"),
    ("BE", "Belgium"),
    ("PL", "Poland"),
    ("CZ", "Czech Republic"),
    ("SE", "Sweden"),
    ("NO", "Norway"),
    ("DK", "Denmark"),
    ("FI", "Finland"),
    ("PT", "Portugal"),
    ("IE", "Ireland"),
    ("LU", "Luxembourg"),
    ("GR", "Greece"),
    ("HU", "Hungary"),
    ("RO", "Romania"),
    ("BG", "Bulgaria"),
    ("HR", "Croatia"),
    ("SK", "Slovakia"),
    ("SI", "Slovenia"),
    ("LT", "Lithuania"),
    ("LV", "Latvia"),
    ("EE", "Estonia"),
    ("CY", "Cyprus"),
    ("MT", "Malta"),
    ("CA", "Canada"),
    ("AU", "Australia"),
    ("NZ", "New Zealand"),
    ("JP", "Japan"),
    ("SG", "Singapore"),
]

# Countries enabled by default (DACH region)
DEFAULT_ENABLED = ["DE", "AT", "CH"]


def upgrade() -> None:
    # Create country table
    op.create_table(
        "country",
        sa.Column("code", sa.String(length=2), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("position", sa.Integer(), nullable=False, server_default="999"),
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_country_code"), "country", ["code"], unique=True)
    op.create_index(
        op.f("ix_country_is_enabled"), "country", ["is_enabled"], unique=False
    )
    op.create_index(op.f("ix_country_position"), "country", ["position"], unique=False)

    # Seed default countries
    for idx, (code, name) in enumerate(DEFAULT_COUNTRIES):
        is_enabled = code in DEFAULT_ENABLED
        position = DEFAULT_ENABLED.index(code) if is_enabled else 999
        op.execute(
            f"""
            INSERT INTO country (code, name, is_enabled, position)
            VALUES ('{code}', '{name}', {str(is_enabled).lower()}, {position})
        """
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_country_position"), table_name="country")
    op.drop_index(op.f("ix_country_is_enabled"), table_name="country")
    op.drop_index(op.f("ix_country_code"), table_name="country")
    op.drop_table("country")
