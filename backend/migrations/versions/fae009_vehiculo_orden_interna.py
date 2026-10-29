"""vehiculo en orden interna

Revision ID: fae009
Revises: fae008
"""
from alembic import op
import sqlalchemy as sa

revision = "fae009"
down_revision = "fae008"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("ordenes_internas", sa.Column("vehiculo_id", sa.Integer(), sa.ForeignKey("vehiculos.id", ondelete="SET NULL"), nullable=True))

def downgrade():
    op.drop_column("ordenes_internas", "vehiculo_id")
