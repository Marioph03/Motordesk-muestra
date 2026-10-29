"""link factura to albaran venta

Revision ID: b8d2e5f7a901
Revises: 7a91c3e4d6f8
Create Date: 2026-09-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8d2e5f7a901"
down_revision: Union[str, Sequence[str], None] = "7a91c3e4d6f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "facturas",
        sa.Column("albaran_venta_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_facturas_albaran_venta_id",
        "facturas",
        "albaranes_venta",
        ["albaran_venta_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_facturas_albaran_venta_id"),
        "facturas",
        ["albaran_venta_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_facturas_albaran_venta_id"), table_name="facturas")
    op.drop_constraint("fk_facturas_albaran_venta_id", "facturas", type_="foreignkey")
    op.drop_column("facturas", "albaran_venta_id")
