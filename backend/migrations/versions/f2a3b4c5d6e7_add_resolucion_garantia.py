"""add resolucion garantia

Revision ID: f2a3b4c5d6e7
Revises: e1a2b3c4d5e6
Create Date: 2026-08-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "e1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ordenes_reparacion",
        sa.Column("resolucion_garantia", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("ordenes_reparacion", "resolucion_garantia")
