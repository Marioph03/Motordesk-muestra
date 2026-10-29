"""Unifica las ramas de migración de Facturae y comisiones de factura.

Revision ID: fb1a3e6d9c42
Revises: d6e3b1f4a902, fae001
Create Date: 2026-09-20
"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "fb1a3e6d9c42"
down_revision: Union[str, Sequence[str], None] = (
    "d6e3b1f4a902",
    "fae001",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge-only revision; both branches already define their schema changes."""


def downgrade() -> None:
    """Merge-only revision; schema changes belong to the parent revisions."""
