"""Add address detail and notes fields to suppliers.

Revision ID: b7c2d8e4f901
Revises: fca4e8b9d012
Create Date: 2026-09-21
"""

from alembic import op
import sqlalchemy as sa


revision = "b7c2d8e4f901"
down_revision = "fca4e8b9d012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("proveedores", sa.Column("ciudad", sa.String(length=100), nullable=True))
    op.add_column("proveedores", sa.Column("provincia", sa.String(length=100), nullable=True))
    op.add_column("proveedores", sa.Column("codigo_postal", sa.String(length=10), nullable=True))
    op.add_column("proveedores", sa.Column("observaciones", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("proveedores", "observaciones")
    op.drop_column("proveedores", "codigo_postal")
    op.drop_column("proveedores", "provincia")
    op.drop_column("proveedores", "ciudad")
