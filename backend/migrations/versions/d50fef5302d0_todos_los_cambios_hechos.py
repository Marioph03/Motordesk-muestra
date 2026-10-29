"""Todos los cambios hechos

Revision ID: d50fef5302d0
Revises: 8848693aa6f7
Create Date: 2026-07-06 14:13:46.997595

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d50fef5302d0"
down_revision: Union[str, Sequence[str], None] = "8848693aa6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "ordenes_reparacion",
        sa.Column(
            "tipo",
            sa.String(length=2),
            nullable=False,
            server_default="TU"
        )
    )

    op.add_column(
        "ordenes_reparacion",
        sa.Column(
            "subtotal",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            server_default="0"
        )
    )

    op.add_column(
        "ordenes_reparacion",
        sa.Column(
            "descuento_porcentaje",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            server_default="0"
        )
    )

    op.drop_column(
        "ordenes_reparacion",
        "descuento"
    )

    # Eliminar los valores por defecto una vez creadas las columnas
    op.alter_column(
        "ordenes_reparacion",
        "tipo",
        server_default=None
    )

    op.alter_column(
        "ordenes_reparacion",
        "subtotal",
        server_default=None
    )

    op.alter_column(
        "ordenes_reparacion",
        "descuento_porcentaje",
        server_default=None
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.add_column(
        "ordenes_reparacion",
        sa.Column(
            "descuento",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            server_default="0"
        )
    )

    op.drop_column(
        "ordenes_reparacion",
        "descuento_porcentaje"
    )

    op.drop_column(
        "ordenes_reparacion",
        "subtotal"
    )

    op.drop_column(
        "ordenes_reparacion",
        "tipo"
    )