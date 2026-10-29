"""reparar tablas de cobros y VERI*FACTU

Revision ID: f4b7c91a2d30
Revises: 2ee4d39cc458
Create Date: 2026-08-07
"""

from alembic import op
import sqlalchemy as sa


revision = "f4b7c91a2d30"
down_revision = "2ee4d39cc458"
branch_labels = None
depends_on = None


def _tablas_existentes() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    tablas = _tablas_existentes()

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
        op.create_index(
            op.f("ix_pagos_factura_id"), "pagos_factura", ["id"], unique=False
        )

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
            sa.ForeignKeyConstraint(
                ["factura_id"], ["facturas.id"], ondelete="RESTRICT"
            ),
            sa.UniqueConstraint("hash_registro"),
        )
        op.create_index(
            op.f("ix_registros_verifactu_id"),
            "registros_verifactu",
            ["id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_registros_verifactu_factura_id"),
            "registros_verifactu",
            ["factura_id"],
            unique=False,
        )


def downgrade() -> None:
    # Esta migración restaura tablas que una migración anterior eliminó por error.
    # No se eliminan datos de cobros o registros durante una reversión.
    pass
