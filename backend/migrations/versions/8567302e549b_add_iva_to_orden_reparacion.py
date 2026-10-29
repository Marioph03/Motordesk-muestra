"""add iva to orden_reparacion

Revision ID: 8567302e549b
Revises: 346ed696b244
Create Date: 2026-07-22 14:22:04.421738

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8567302e549b"
down_revision: Union[str, Sequence[str], None] = "346ed696b244"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "ordenes_reparacion",
        sa.Column(
            "iva",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0"
        )
    )

    # Elimina el valor por defecto para futuras inserciones
    op.alter_column(
        "ordenes_reparacion",
        "iva",
        server_default=None
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "ordenes_reparacion",
        "iva"
    )