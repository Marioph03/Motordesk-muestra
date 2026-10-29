"""add albaranes venta

Revision ID: 7a91c3e4d6f8
Revises: 6efc698b6ae0
Create Date: 2026-09-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7a91c3e4d6f8"
down_revision: Union[str, Sequence[str], None] = "6efc698b6ae0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "albaranes_venta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.String(length=50), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("estado", sa.String(length=30), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_albaranes_venta_id"), "albaranes_venta", ["id"], unique=False)
    op.create_index(op.f("ix_albaranes_venta_numero"), "albaranes_venta", ["numero"], unique=True)
    op.create_index(op.f("ix_albaranes_venta_cliente_id"), "albaranes_venta", ["cliente_id"], unique=False)
    op.create_index(op.f("ix_albaranes_venta_estado"), "albaranes_venta", ["estado"], unique=False)

    op.create_table(
        "lineas_albaran_venta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("albaran_id", sa.Integer(), nullable=False),
        sa.Column("articulo_stock_id", sa.Integer(), nullable=False),
        sa.Column("referencia", sa.String(length=100), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=False),
        sa.Column("cantidad", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("descuento_porcentaje", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["albaran_id"], ["albaranes_venta.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["articulo_stock_id"], ["articulos_stock.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lineas_albaran_venta_id"), "lineas_albaran_venta", ["id"], unique=False)
    op.create_index(op.f("ix_lineas_albaran_venta_albaran_id"), "lineas_albaran_venta", ["albaran_id"], unique=False)
    op.create_index(op.f("ix_lineas_albaran_venta_articulo_stock_id"), "lineas_albaran_venta", ["articulo_stock_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_lineas_albaran_venta_articulo_stock_id"), table_name="lineas_albaran_venta")
    op.drop_index(op.f("ix_lineas_albaran_venta_albaran_id"), table_name="lineas_albaran_venta")
    op.drop_index(op.f("ix_lineas_albaran_venta_id"), table_name="lineas_albaran_venta")
    op.drop_table("lineas_albaran_venta")
    op.drop_index(op.f("ix_albaranes_venta_estado"), table_name="albaranes_venta")
    op.drop_index(op.f("ix_albaranes_venta_cliente_id"), table_name="albaranes_venta")
    op.drop_index(op.f("ix_albaranes_venta_numero"), table_name="albaranes_venta")
    op.drop_index(op.f("ix_albaranes_venta_id"), table_name="albaranes_venta")
    op.drop_table("albaranes_venta")
