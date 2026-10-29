"""codigos visibles para vehiculos

Revision ID: fae012
Revises: fae011
"""
from alembic import op
import sqlalchemy as sa


revision = "fae012"
down_revision = "fae011"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("vehiculos", sa.Column("codigo", sa.String(length=20), nullable=True))
    op.execute("UPDATE vehiculos SET codigo = 'VEH-' || LPAD(id::text, 6, '0')")
    op.create_unique_constraint("uq_vehiculos_codigo", "vehiculos", ["codigo"])
    op.create_index("ix_vehiculos_codigo", "vehiculos", ["codigo"])


def downgrade():
    op.drop_index("ix_vehiculos_codigo", table_name="vehiculos")
    op.drop_constraint("uq_vehiculos_codigo", "vehiculos", type_="unique")
    op.drop_column("vehiculos", "codigo")
