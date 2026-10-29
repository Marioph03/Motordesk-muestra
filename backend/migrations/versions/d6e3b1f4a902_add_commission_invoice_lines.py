"""Add fiscal categories for mixed sales and commission invoices.

Revision ID: d6e3b1f4a902
Revises: c4f8a2d9b713
Create Date: 2026-09-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d6e3b1f4a902"
down_revision: Union[str, Sequence[str], None] = "c4f8a2d9b713"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "factura_lineas",
        sa.Column(
            "categoria_fiscal",
            sa.String(length=30),
            nullable=False,
            server_default="VENTA_SERVICIO",
        ),
    )
    op.add_column(
        "factura_lineas",
        sa.Column("motivo_exencion", sa.String(length=255), nullable=True),
    )
    op.alter_column(
        "factura_lineas",
        "categoria_fiscal",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("factura_lineas", "motivo_exencion")
    op.drop_column("factura_lineas", "categoria_fiscal")
