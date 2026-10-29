"""porcentajes de IVA e IRPF en facturas de proveedor

Revision ID: fae010
Revises: fae009
"""
from alembic import op
import sqlalchemy as sa

revision = "fae010"
down_revision = "fae009"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("facturas_proveedor", sa.Column("porcentaje_iva", sa.Numeric(5, 2), nullable=False, server_default="0"))
    op.add_column("facturas_proveedor", sa.Column("porcentaje_retencion", sa.Numeric(5, 2), nullable=False, server_default="0"))
    op.add_column("facturas_proveedor", sa.Column("retencion_irpf", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.execute("UPDATE facturas_proveedor SET porcentaje_iva = CASE WHEN base_imponible > 0 THEN ROUND(iva * 100.0 / base_imponible, 2) ELSE 0 END")


def downgrade():
    op.drop_column("facturas_proveedor", "retencion_irpf")
    op.drop_column("facturas_proveedor", "porcentaje_retencion")
    op.drop_column("facturas_proveedor", "porcentaje_iva")
