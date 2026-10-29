"""Añadir descuento a ordenes

Revision ID: 8848693aa6f7
Revises: 0a60529a8a56
Create Date: 2026-07-06 13:39:41.823859
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8848693aa6f7'
down_revision: Union[str, Sequence[str], None] = '0a60529a8a56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'ordenes_reparacion',
        sa.Column(
            'descuento',
            sa.Numeric(10, 2),
            nullable=False,
            server_default='0'
        )
    )

    op.add_column(
        'ordenes_reparacion',
        sa.Column(
            'garantia',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false()
        )
    )

    op.add_column(
        'ordenes_reparacion',
        sa.Column(
            'garantia_meses',
            sa.Integer(),
            nullable=True
        )
    )

    op.add_column(
        'ordenes_reparacion',
        sa.Column(
            'base_imponible',
            sa.Numeric(10, 2),
            nullable=False,
            server_default='0'
        )
    )

    # Eliminar los defaults una vez rellenadas las filas existentes
    op.alter_column(
        'ordenes_reparacion',
        'descuento',
        server_default=None
    )

    op.alter_column(
        'ordenes_reparacion',
        'garantia',
        server_default=None
    )

    op.alter_column(
        'ordenes_reparacion',
        'base_imponible',
        server_default=None
    )


def downgrade() -> None:
    op.drop_column('ordenes_reparacion', 'base_imponible')
    op.drop_column('ordenes_reparacion', 'garantia_meses')
    op.drop_column('ordenes_reparacion', 'garantia')
    op.drop_column('ordenes_reparacion', 'descuento')