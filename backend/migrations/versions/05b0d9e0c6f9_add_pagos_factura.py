"""add pagos factura

Revision ID: 05b0d9e0c6f9
Revises: e71d2a4c9f80
Create Date: 2026-08-07 10:41:04.608025

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "05b0d9e0c6f9"
down_revision: Union[str, Sequence[str], None] = "e71d2a4c9f80"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ---------------------------------------------------------
    # 1. Añadir estado de cobro a las facturas existentes
    # ---------------------------------------------------------

    op.add_column(
        "facturas",
        sa.Column(
            "estado_cobro",
            sa.String(length=20),
            nullable=False,
            server_default="PENDIENTE"
        )
    )

    # ---------------------------------------------------------
    # 2. Crear tabla de pagos/cobros de factura
    # ---------------------------------------------------------

    op.create_table(
        "pagos_factura",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "factura_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "importe",
            sa.Numeric(precision=10, scale=2),
            nullable=False
        ),

        sa.Column(
            "metodo_pago",
            sa.String(length=30),
            nullable=False
        ),

        sa.Column(
            "referencia",
            sa.String(length=100),
            nullable=True
        ),

        sa.Column(
            "observaciones",
            sa.Text(),
            nullable=True
        ),

        sa.Column(
            "fecha_pago",
            sa.DateTime(),
            nullable=False
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ["factura_id"],
            ["facturas.id"]
        ),

        sa.PrimaryKeyConstraint("id")
    )

    # Índice equivalente a index=True del modelo
    op.create_index(
        op.f("ix_pagos_factura_id"),
        "pagos_factura",
        ["id"],
        unique=False
    )

    # Una vez actualizadas las facturas existentes,
    # eliminamos el DEFAULT de la BD.
    # El modelo SQLAlchemy seguirá asignando PENDIENTE
    # a las facturas nuevas.
    op.alter_column(
        "facturas",
        "estado_cobro",
        server_default=None
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Primero eliminar la tabla que depende de facturas
    op.drop_index(
        op.f("ix_pagos_factura_id"),
        table_name="pagos_factura"
    )

    op.drop_table(
        "pagos_factura"
    )

    # Después eliminar la columna
    op.drop_column(
        "facturas",
        "estado_cobro"
    )