"""Crear tablas facturacion

Revision ID: 99ae3a86b429
Revises: d50fef5302d0
Create Date: 2026-07-07 12:26:52.698991

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "99ae3a86b429"
down_revision: Union[str, Sequence[str], None] = "d50fef5302d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "facturas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.String(length=30), nullable=False),
        sa.Column("tipo_documento", sa.String(length=20), nullable=False),
        sa.Column("tipo_factura", sa.String(length=20), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("vehiculo_id", sa.Integer(), nullable=True),
        sa.Column("orden_id", sa.Integer(), nullable=True),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("descuento_porcentaje", sa.Numeric(5, 2), nullable=False),
        sa.Column("base_imponible", sa.Numeric(10, 2), nullable=False),
        sa.Column("iva", sa.Numeric(5, 2), nullable=False),
        sa.Column("cuota_iva", sa.Numeric(10, 2), nullable=False),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("fecha_emision", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("enviada_verifactu", sa.Boolean(), nullable=False),
        sa.Column("hash_verifactu", sa.String(length=255), nullable=True),
        sa.Column("fecha_envio_verifactu", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["orden_id"], ["ordenes_reparacion.id"]),
        sa.ForeignKeyConstraint(["vehiculo_id"], ["vehiculos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("numero")
    )

    op.create_index(
        op.f("ix_facturas_id"),
        "facturas",
        ["id"],
        unique=False
    )

    op.create_index(
        "ix_facturas_numero",
        "facturas",
        ["numero"],
        unique=True
    )

    op.create_table(
        "factura_lineas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("factura_id", sa.Integer(), nullable=False),
        sa.Column("origen", sa.String(length=20), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=False),
        sa.Column("cantidad", sa.Numeric(10, 2), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(10, 2), nullable=False),
        sa.Column("descuento_porcentaje", sa.Numeric(5, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("iva", sa.Numeric(5, 2), nullable=False),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(["factura_id"], ["facturas.id"]),
        sa.PrimaryKeyConstraint("id")
    )

    op.create_index(
        op.f("ix_factura_lineas_id"),
        "factura_lineas",
        ["id"],
        unique=False
    )

    op.create_index(
        "ix_factura_lineas_factura_id",
        "factura_lineas",
        ["factura_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_factura_lineas_factura_id",
        table_name="factura_lineas"
    )

    op.drop_index(
        op.f("ix_factura_lineas_id"),
        table_name="factura_lineas"
    )

    op.drop_table("factura_lineas")

    op.drop_index(
        "ix_facturas_numero",
        table_name="facturas"
    )

    op.drop_index(
        op.f("ix_facturas_id"),
        table_name="facturas"
    )

    op.drop_table("facturas")