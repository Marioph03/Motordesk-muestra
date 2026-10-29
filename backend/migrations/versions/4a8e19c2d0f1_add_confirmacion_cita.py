"""add confirmacion cita

Revision ID: 4a8e19c2d0f1
Revises: 3db5fc8d545d
"""
from alembic import op
import sqlalchemy as sa

revision = "4a8e19c2d0f1"
down_revision = "3db5fc8d545d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("citas", sa.Column("fecha_confirmacion", sa.DateTime(), nullable=True))
    op.add_column("citas", sa.Column("canal_confirmacion", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("citas", "canal_confirmacion")
    op.drop_column("citas", "fecha_confirmacion")
