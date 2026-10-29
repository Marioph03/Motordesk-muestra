"""Restaurar tablas de cobros y VERI*FACTU eliminadas por una migración previa.

Revision ID: c6d7e8f9a0b1
Revises: b5c6d7e8f9a0
Create Date: 2026-08-18
"""

from alembic import op
import sqlalchemy as sa


revision = "c6d7e8f9a0b1"
down_revision = "b5c6d7e8f9a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tablas = set(sa.inspect(op.get_bind()).get_table_names())

    if "pagos_factura" not in tablas:
        op.create_table(
            "pagos_factura",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("factura_id", sa.Integer(), nullable=False),
            sa.Column("importe", sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column("metodo_pago", sa.String(length=30), nullable=False),
            sa.Column("referencia", sa.String(length=100), nullable=True),
            sa.Column("observaciones", sa.Text(), nullable=True),
            sa.Column("fecha_pago", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.CheckConstraint("importe > 0", name="ck_pagos_factura_importe_positivo"),
            sa.CheckConstraint(
                "metodo_pago IN ('EFECTIVO', 'TARJETA', 'TRANSFERENCIA', 'BIZUM', 'OTRO')",
                name="ck_pagos_factura_metodo_pago_valido",
            ),
            sa.ForeignKeyConstraint(["factura_id"], ["facturas.id"]),
        )
        op.create_index("ix_pagos_factura_id", "pagos_factura", ["id"])

    if "registros_verifactu" not in tablas:
        op.create_table(
            "registros_verifactu",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("factura_id", sa.Integer(), nullable=False),
            sa.Column("tipo_registro", sa.String(length=20), nullable=False),
            sa.Column("estado", sa.String(length=30), nullable=False),
            sa.Column("hash_registro", sa.String(length=64), nullable=False),
            sa.Column("hash_anterior", sa.String(length=64), nullable=True),
            sa.Column("factura_anterior_numero", sa.String(length=100), nullable=True),
            sa.Column("factura_anterior_fecha", sa.String(length=10), nullable=True),
            sa.Column("xml_registro", sa.Text(), nullable=False),
            sa.Column("respuesta_aeat", sa.Text(), nullable=True),
            sa.Column("codigo_respuesta", sa.String(length=100), nullable=True),
            sa.Column("mensaje_error", sa.Text(), nullable=True),
            sa.Column("intentos_envio", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("fecha_generacion", sa.DateTime(timezone=True), nullable=False),
            sa.Column("fecha_ultimo_intento", sa.DateTime(timezone=True), nullable=True),
            sa.Column("fecha_aceptacion", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["factura_id"], ["facturas.id"], ondelete="RESTRICT"),
            sa.UniqueConstraint("hash_registro"),
        )
        op.create_index("ix_registros_verifactu_id", "registros_verifactu", ["id"])
        op.create_index(
            "ix_registros_verifactu_factura_id",
            "registros_verifactu",
            ["factura_id"],
        )


def downgrade() -> None:
    # No se eliminan registros contables ni cobros en una reversión.
    pass
