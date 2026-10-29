"""add provincia to clientes

Revision ID: 9a1f6c2d4e8b
Revises: 8e34025998d9
Create Date: 2026-09-10 12:40:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "9a1f6c2d4e8b"
down_revision: Union[str, Sequence[str], None] = "8e34025998d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Añade Provincia sin modificar los clientes ya registrados."""
    op.add_column(
        "clientes",
        sa.Column("provincia", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    """Revierte únicamente la columna añadida por esta revisión."""
    op.drop_column("clientes", "provincia")
