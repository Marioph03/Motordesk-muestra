"""add registros verifactu

Revision ID: 2ee4d39cc458
Revises: 8c3d1f7a92be
Create Date: 2026-08-07 11:50:02.996324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2ee4d39cc458'
down_revision: Union[str, Sequence[str], None] = '8c3d1f7a92be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
    op.drop_index(
        op.f("ix_registros_verifactu_factura_id"),
        table_name="registros_verifactu",
    )
    op.drop_index(
        op.f("ix_registros_verifactu_id"),
        table_name="registros_verifactu",
    )
    op.drop_table("registros_verifactu")
