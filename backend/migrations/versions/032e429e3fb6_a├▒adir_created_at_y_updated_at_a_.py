"""Añadir created_at y updated_at a factura_lineas

Revision ID: 032e429e3fb6
Revises: d83b0d713df3
Create Date: 2026-07-07 14:05:20.650931

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "032e429e3fb6"
down_revision: Union[str, Sequence[str], None] = "d83b0d713df3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.add_column(
        "factura_lineas",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now()
        )
    )

    op.add_column(
        "factura_lineas",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now()
        )
    )

    op.alter_column(
        "factura_lineas",
        "created_at",
        server_default=None
    )

    op.alter_column(
        "factura_lineas",
        "updated_at",
        server_default=None
    )


def downgrade() -> None:

    op.drop_column(
        "factura_lineas",
        "updated_at"
    )

    op.drop_column(
        "factura_lineas",
        "created_at"
    )