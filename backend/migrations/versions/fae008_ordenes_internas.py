"""ordenes internas

Revision ID: fae008
Revises: fae007
"""
from alembic import op
import sqlalchemy as sa

revision = "fae008"
down_revision = "fae007"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("ordenes_internas", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("numero", sa.String(24), nullable=False, unique=True), sa.Column("titulo", sa.String(200), nullable=False), sa.Column("categoria", sa.String(50), nullable=False), sa.Column("referencia_activo", sa.String(200)), sa.Column("descripcion", sa.Text(), nullable=False), sa.Column("estado", sa.String(20), nullable=False), sa.Column("responsable_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="SET NULL")), sa.Column("coste_total", sa.Numeric(12,2), nullable=False, server_default="0"), sa.Column("fecha_apertura", sa.DateTime(), nullable=False), sa.Column("fecha_cierre", sa.DateTime()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_index("ix_ordenes_internas_numero", "ordenes_internas", ["numero"])
    op.create_table("lineas_orden_interna", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("orden_interna_id", sa.Integer(), sa.ForeignKey("ordenes_internas.id", ondelete="CASCADE"), nullable=False), sa.Column("tipo", sa.String(12), nullable=False), sa.Column("articulo_stock_id", sa.Integer(), sa.ForeignKey("articulos_stock.id", ondelete="SET NULL")), sa.Column("referencia", sa.String(100)), sa.Column("descripcion", sa.String(500), nullable=False), sa.Column("cantidad", sa.Numeric(12,2), nullable=False), sa.Column("coste_unitario", sa.Numeric(12,2), nullable=False))
    op.create_index("ix_lineas_orden_interna_orden_interna_id", "lineas_orden_interna", ["orden_interna_id"])

def downgrade():
    op.drop_index("ix_lineas_orden_interna_orden_interna_id", table_name="lineas_orden_interna")
    op.drop_table("lineas_orden_interna")
    op.drop_index("ix_ordenes_internas_numero", table_name="ordenes_internas")
    op.drop_table("ordenes_internas")
