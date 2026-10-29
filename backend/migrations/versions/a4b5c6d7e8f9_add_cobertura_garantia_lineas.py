"""add cobertura garantia lineas

Revision ID: a4b5c6d7e8f9
Revises: f2a3b4c5d6e7
Create Date: 2026-08-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a4b5c6d7e8f9"
down_revision: Union[str, Sequence[str], None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("mano_obra", sa.Column("cubierto_garantia", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("piezas", sa.Column("cubierto_garantia", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column("mano_obra", "cubierto_garantia", server_default=None)
    op.alter_column("piezas", "cubierto_garantia", server_default=None)

def downgrade() -> None:
    op.drop_column("piezas", "cubierto_garantia")
    op.drop_column("mano_obra", "cubierto_garantia")
