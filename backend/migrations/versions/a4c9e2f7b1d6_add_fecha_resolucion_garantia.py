"""add fecha resolucion garantia

Revision ID: a4c9e2f7b1d6
Revises: f98d8b56d463
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4c9e2f7b1d6"
down_revision: Union[str, Sequence[str], None] = "f98d8b56d463"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ordenes_reparacion",
        sa.Column("fecha_resolucion_garantia", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_ordenes_reparacion_fecha_resolucion_garantia",
        "ordenes_reparacion",
        ["fecha_resolucion_garantia"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ordenes_reparacion_fecha_resolucion_garantia",
        table_name="ordenes_reparacion",
    )
    op.drop_column("ordenes_reparacion", "fecha_resolucion_garantia")
