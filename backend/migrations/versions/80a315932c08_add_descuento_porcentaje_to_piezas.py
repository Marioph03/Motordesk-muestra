"""add descuento_porcentaje to piezas

Revision ID: 80a315932c08
Revises: 429a23701a36
Create Date: 2026-07-23 13:57:51.604517

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "80a315932c08"
down_revision: Union[str, Sequence[str], None] = "429a23701a36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "piezas",
        sa.Column(
            "descuento_porcentaje",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="0"
        )
    )

    op.alter_column(
        "piezas",
        "descuento_porcentaje",
        server_default=None
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "piezas",
        "descuento_porcentaje"
    )