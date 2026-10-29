"""productos varios sin control de stock

Revision ID: fae007
Revises: fae006
"""
from alembic import op
import sqlalchemy as sa

revision = "fae007"
down_revision = "fae006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("articulos_stock", sa.Column("controla_stock", sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    op.drop_column("articulos_stock", "controla_stock")
