"""add importes garantia

Revision ID: b5c6d7e8f9a0
Revises: a4b5c6d7e8f9
Create Date: 2026-08-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "b5c6d7e8f9a0"
down_revision: Union[str, Sequence[str], None] = "a4b5c6d7e8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    for name in ('coste_asumido_taller', 'trabajos_no_cubiertos', 'iva_cliente_garantia', 'total_cliente_garantia'):
        op.add_column('ordenes_reparacion', sa.Column(name, sa.Numeric(10, 2), nullable=False, server_default='0'))
        op.alter_column('ordenes_reparacion', name, server_default=None)

def downgrade() -> None:
    for name in ('total_cliente_garantia', 'iva_cliente_garantia', 'trabajos_no_cubiertos', 'coste_asumido_taller'):
        op.drop_column('ordenes_reparacion', name)
