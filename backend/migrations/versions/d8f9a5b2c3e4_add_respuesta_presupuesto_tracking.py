"""add respuesta presupuesto tracking

Revision ID: d8f9a5b2c3e4
Revises: c7e8f4a1b2d3
Create Date: 2026-08-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d8f9a5b2c3e4"
down_revision: Union[str, Sequence[str], None] = "c7e8f4a1b2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ordenes_reparacion",
        sa.Column("fecha_respuesta_presupuesto", sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("ordenes_reparacion", "fecha_respuesta_presupuesto")
