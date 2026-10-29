"""add envio presupuesto tracking

Revision ID: c7e8f4a1b2d3
Revises: e4936bb56948
Create Date: 2026-08-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7e8f4a1b2d3"
down_revision: Union[str, Sequence[str], None] = "e4936bb56948"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ordenes_reparacion",
        sa.Column("fecha_envio_presupuesto", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "ordenes_reparacion",
        sa.Column("canal_envio_presupuesto", sa.String(length=20), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("ordenes_reparacion", "canal_envio_presupuesto")
    op.drop_column("ordenes_reparacion", "fecha_envio_presupuesto")
