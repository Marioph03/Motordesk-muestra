"""add default bank account for transfer collections

Revision ID: f2a9c6d4e8b1
Revises: e7f3a1b9c5d2
Create Date: 2026-09-11 15:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f2a9c6d4e8b1"
down_revision: Union[str, Sequence[str], None] = "e7f3a1b9c5d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Añade una cuenta opcional sin modificar cobros ya registrados."""
    op.add_column(
        "configuracion_documentos",
        sa.Column("iban_cobros", sa.String(length=34), nullable=True),
    )


def downgrade() -> None:
    """Revierte exclusivamente la preferencia de cuenta bancaria."""
    op.drop_column("configuracion_documentos", "iban_cobros")
