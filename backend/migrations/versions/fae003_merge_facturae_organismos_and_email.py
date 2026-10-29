"""Merge Facturae organization directory and email OAuth revisions.

Revision ID: fae003
Revises: fae002, d3e4f5a6b7c8
Create Date: 2026-09-23
"""

from typing import Sequence, Union


revision: str = "fae003"
down_revision: Union[str, Sequence[str], None] = ("fae002", "d3e4f5a6b7c8")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge-only revision."""


def downgrade() -> None:
    """Merge-only revision."""
