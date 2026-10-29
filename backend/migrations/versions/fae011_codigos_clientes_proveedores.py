"""códigos visibles para clientes y proveedores

Revision ID: fae011
Revises: fae010
"""
from alembic import op
import sqlalchemy as sa


revision = "fae011"
down_revision = "fae010"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("clientes", sa.Column("codigo", sa.String(length=20), nullable=True))
    op.add_column("proveedores", sa.Column("codigo", sa.String(length=20), nullable=True))

    op.execute("UPDATE clientes SET codigo = 'CL-' || LPAD(id::text, 6, '0')")
    op.execute("UPDATE proveedores SET codigo = 'PRO-' || LPAD(id::text, 6, '0')")

    op.create_unique_constraint("uq_clientes_codigo", "clientes", ["codigo"])
    op.create_index("ix_clientes_codigo", "clientes", ["codigo"])
    op.create_unique_constraint("uq_proveedores_codigo", "proveedores", ["codigo"])
    op.create_index("ix_proveedores_codigo", "proveedores", ["codigo"])


def downgrade():
    op.drop_index("ix_proveedores_codigo", table_name="proveedores")
    op.drop_constraint("uq_proveedores_codigo", "proveedores", type_="unique")
    op.drop_column("proveedores", "codigo")
    op.drop_index("ix_clientes_codigo", table_name="clientes")
    op.drop_constraint("uq_clientes_codigo", "clientes", type_="unique")
    op.drop_column("clientes", "codigo")
