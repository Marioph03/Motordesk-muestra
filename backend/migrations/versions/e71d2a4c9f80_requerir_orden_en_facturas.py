"""Requerir una orden para cada factura.

Revision ID: e71d2a4c9f80
Revises: 39304fbf25de
Create Date: 2026-08-06
"""

from alembic import op
import sqlalchemy as sa


revision = "e71d2a4c9f80"
down_revision = "39304fbf25de"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "facturas",
        "orden_id",
        existing_type=sa.Integer(),
        nullable=False
    )


def downgrade() -> None:
    op.alter_column(
        "facturas",
        "orden_id",
        existing_type=sa.Integer(),
        nullable=True
    )
