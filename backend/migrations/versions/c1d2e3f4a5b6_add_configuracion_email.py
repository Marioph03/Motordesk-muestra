"""add encrypted email configuration per company

Revision ID: c1d2e3f4a5b6
Revises: b7c2d8e4f901
"""
import sqlalchemy as sa
from alembic import op

revision = "c1d2e3f4a5b6"
down_revision = "b7c2d8e4f901"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("configuracion_email",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("empresa_id", sa.Integer(), sa.ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("proveedor", sa.String(30), nullable=False, server_default="gmail"),
        sa.Column("host", sa.String(255), nullable=False), sa.Column("puerto", sa.Integer(), nullable=False, server_default="587"),
        sa.Column("seguridad", sa.String(20), nullable=False, server_default="starttls"), sa.Column("usuario", sa.String(255), nullable=False),
        sa.Column("remitente", sa.String(255), nullable=True), sa.Column("password_cifrada", sa.Text(), nullable=False))
    op.create_index("ix_configuracion_email_empresa_id", "configuracion_email", ["empresa_id"])

def downgrade():
    op.drop_index("ix_configuracion_email_empresa_id", table_name="configuracion_email")
    op.drop_table("configuracion_email")
