"""Merge Facturae and sales-commission invoice migration heads.

Revision ID: fb2c7d1a9e45
Revises: d6e3b1f4a902, fae001
Create Date: 2026-09-18
"""

from typing import Sequence, Union


revision: str = "fb2c7d1a9e45"
down_revision: Union[str, Sequence[str], None] = (
    "d6e3b1f4a902",
    "fae001",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Join two already independent schema changes."""


def downgrade() -> None:
    """The merge revision has no schema operation of its own."""
