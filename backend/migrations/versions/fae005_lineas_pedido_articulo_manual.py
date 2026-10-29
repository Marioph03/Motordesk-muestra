"""Allow purchase-order lines for articles not yet in stock."""

from alembic import op
import sqlalchemy as sa


revision = "fae005"
down_revision = "fae004"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "lineas_pedido_compra",
        "articulo_stock_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade():
    op.alter_column(
        "lineas_pedido_compra",
        "articulo_stock_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
