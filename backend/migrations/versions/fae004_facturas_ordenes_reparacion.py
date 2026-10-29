"""Allow one repair invoice to include multiple orders."""
from alembic import op
import sqlalchemy as sa
revision = "fae004"
down_revision = "fae003"
branch_labels = None
depends_on = None
def upgrade():
    op.create_table("facturas_ordenes_reparacion", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("factura_id", sa.Integer(), sa.ForeignKey("facturas.id", ondelete="CASCADE"), nullable=False), sa.Column("orden_id", sa.Integer(), sa.ForeignKey("ordenes_reparacion.id"), nullable=False, unique=True), sa.UniqueConstraint("factura_id", "orden_id", name="uq_factura_orden_reparacion"))
    op.create_index("ix_facturas_ordenes_reparacion_factura_id", "facturas_ordenes_reparacion", ["factura_id"])
    op.create_index("ix_facturas_ordenes_reparacion_orden_id", "facturas_ordenes_reparacion", ["orden_id"])
def downgrade(): op.drop_table("facturas_ordenes_reparacion")
