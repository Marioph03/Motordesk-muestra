"""Add reusable Facturae recipient directory.

Revision ID: fae002
Revises: fca4e8b9d012
Create Date: 2026-09-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fae002"
down_revision: Union[str, Sequence[str], None] = "fca4e8b9d012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "facturae_organismos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("empresa_id", sa.Integer(), sa.ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("nif", sa.String(length=20), nullable=False),
        sa.Column("direccion", sa.String(length=255), nullable=True),
        sa.Column("codigo_postal", sa.String(length=10), nullable=True),
        sa.Column("ciudad", sa.String(length=100), nullable=True),
        sa.Column("provincia", sa.String(length=100), nullable=True),
        sa.Column("oficina_contable", sa.String(length=10), nullable=False),
        sa.Column("organo_gestor", sa.String(length=10), nullable=False),
        sa.Column("unidad_tramitadora", sa.String(length=10), nullable=False),
        sa.Column("expediente", sa.String(length=100), nullable=True),
        sa.Column("referencia_contrato", sa.String(length=100), nullable=True),
        sa.Column("referencia_receptor", sa.String(length=100), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("empresa_id", "nif", name="uq_facturae_organismo_empresa_nif"),
    )
    op.create_index("ix_facturae_organismos_id", "facturae_organismos", ["id"])
    op.create_index("ix_facturae_organismos_empresa_id", "facturae_organismos", ["empresa_id"])


def downgrade() -> None:
    op.drop_index("ix_facturae_organismos_empresa_id", table_name="facturae_organismos")
    op.drop_index("ix_facturae_organismos_id", table_name="facturae_organismos")
    op.drop_table("facturae_organismos")
