"""add descuento_porcentaje to mano_obra

Revision ID: 429a23701a36
Revises: c9b452dea311
Create Date: 2026-07-23 13:33:54.268729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "429a23701a36"
down_revision: Union[str, Sequence[str], None] = "c9b452dea311"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "mano_obra",
        sa.Column(
            "descuento_porcentaje",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="0"
        )
    )

    op.alter_column(
        "mano_obra",
        "descuento_porcentaje",
        server_default=None
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "mano_obra",
        "descuento_porcentaje"
    )