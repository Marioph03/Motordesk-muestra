"""add vehicle registration date and order entry mileage

Revision ID: b4c8d2e6f1a3
Revises: 9a1f6c2d4e8b
Create Date: 2026-09-11 09:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b4c8d2e6f1a3"
down_revision: Union[str, Sequence[str], None] = "9a1f6c2d4e8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Añade campos opcionales sin alterar vehículos ni órdenes existentes."""
    op.add_column(
        "vehiculos",
        sa.Column("fecha_matriculacion", sa.Date(), nullable=True),
    )
    op.add_column(
        "ordenes_reparacion",
        sa.Column("kilometros_entrada", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Revierte exclusivamente los campos incorporados por esta revisión."""
    op.drop_column("ordenes_reparacion", "kilometros_entrada")
    op.drop_column("vehiculos", "fecha_matriculacion")
