"""Add public-administration recipient data for Facturae.

Revision ID: fae001
Revises: 6efc698b6ae0
"""

from alembic import op
import sqlalchemy as sa


revision = "fae001"
down_revision = "6efc698b6ae0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "facturae_destinos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("factura_id", sa.Integer(), sa.ForeignKey("facturas.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("nif", sa.String(length=20), nullable=False),
        sa.Column("direccion", sa.String(length=255)),
        sa.Column("codigo_postal", sa.String(length=10)),
        sa.Column("ciudad", sa.String(length=100)),
        sa.Column("provincia", sa.String(length=100)),
        sa.Column("oficina_contable", sa.String(length=10), nullable=False),
        sa.Column("organo_gestor", sa.String(length=10), nullable=False),
        sa.Column("unidad_tramitadora", sa.String(length=10), nullable=False),
        sa.Column("expediente", sa.String(length=100)),
        sa.Column("referencia_contrato", sa.String(length=100)),
        sa.Column("referencia_receptor", sa.String(length=100)),
        sa.Column("observaciones", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_facturae_destinos_id", "facturae_destinos", ["id"])
    op.create_index("ix_facturae_destinos_factura_id", "facturae_destinos", ["factura_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_facturae_destinos_factura_id", table_name="facturae_destinos")
    op.drop_index("ix_facturae_destinos_id", table_name="facturae_destinos")
    op.drop_table("facturae_destinos")
