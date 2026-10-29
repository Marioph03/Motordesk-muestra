"""add labor code to warranty work lines

Revision ID: e7f3a1b9c5d2
Revises: b4c8d2e6f1a3
Create Date: 2026-09-11 10:15:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e7f3a1b9c5d2"
down_revision: Union[str, Sequence[str], None] = "b4c8d2e6f1a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Añade el código opcional de operación de garantía por línea."""
    op.add_column(
        "mano_obra",
        sa.Column("codigo_mano_obra", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    """Elimina únicamente el código de mano de obra incorporado."""
    op.drop_column("mano_obra", "codigo_mano_obra")
