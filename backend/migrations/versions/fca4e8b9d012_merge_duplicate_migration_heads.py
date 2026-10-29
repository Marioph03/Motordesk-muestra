"""Unify duplicate Facturae/commission merge revisions.

Revision ID: fca4e8b9d012
Revises: fb1a3e6d9c42, fb2c7d1a9e45
Create Date: 2026-09-21

Both parent revisions are merge-only revisions created independently for the
same two schema branches. This revision contains no DDL: it restores a single
Alembic head while remaining safe for databases that already recorded either
parent revision.
"""

from typing import Sequence, Union


revision: str = "fca4e8b9d012"
down_revision: Union[str, Sequence[str], None] = (
    "fb1a3e6d9c42",
    "fb2c7d1a9e45",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge-only revision; the parent revisions contain no DDL."""


def downgrade() -> None:
    """Merge-only revision; no schema operation is necessary."""
