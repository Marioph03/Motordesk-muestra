"""Clasifica los gastos de las facturas de compra."""

from alembic import op
import sqlalchemy as sa


revision = "fae014"
down_revision = "fae013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("proveedores", "tipo")
    op.add_column(
        "facturas_proveedor",
        sa.Column("tipo_gasto", sa.String(length=30), nullable=False, server_default="COMPRA"),
    )


def downgrade() -> None:
    op.drop_column("facturas_proveedor", "tipo_gasto")
    op.add_column(
        "proveedores",
        sa.Column("tipo", sa.String(length=30), nullable=False, server_default="COMPRA"),
    )
