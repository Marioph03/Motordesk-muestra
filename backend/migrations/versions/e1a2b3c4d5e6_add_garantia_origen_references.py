"""add garantia origen references

Revision ID: e1a2b3c4d5e6
Revises: d8f9a5b2c3e4
Create Date: 2026-08-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "d8f9a5b2c3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ordenes_reparacion",
        sa.Column("orden_origen_garantia_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "ordenes_reparacion",
        sa.Column("factura_origen_garantia_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_orden_garantia_origen",
        "ordenes_reparacion",
        "ordenes_reparacion",
        ["orden_origen_garantia_id"], ["id"],
        ondelete="SET NULL"
    )
    op.create_foreign_key(
        "fk_factura_garantia_origen",
        "ordenes_reparacion",
        "facturas",
        ["factura_origen_garantia_id"], ["id"],
        ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_factura_garantia_origen", "ordenes_reparacion", type_="foreignkey")
    op.drop_constraint("fk_orden_garantia_origen", "ordenes_reparacion", type_="foreignkey")
    op.drop_column("ordenes_reparacion", "factura_origen_garantia_id")
    op.drop_column("ordenes_reparacion", "orden_origen_garantia_id")
