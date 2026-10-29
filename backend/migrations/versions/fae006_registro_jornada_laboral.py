"""registro jornada laboral

Revision ID: fae006
Revises: fae005
"""
from alembic import op
import sqlalchemy as sa

revision = "fae006"
down_revision = "fae005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("usuarios", sa.Column("hora_entrada_predeterminada", sa.Time(), nullable=False, server_default="08:00:00"))
    op.add_column("usuarios", sa.Column("hora_salida_predeterminada", sa.Time(), nullable=False, server_default="16:00:00"))
    op.create_table("registros_jornada", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False), sa.Column("fecha", sa.Date(), nullable=False), sa.Column("presente", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("hora_entrada", sa.Time()), sa.Column("hora_salida", sa.Time()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("usuario_id", "fecha", name="uq_registro_jornada_usuario_fecha"))
    op.create_index("ix_registros_jornada_usuario_id", "registros_jornada", ["usuario_id"])
    op.create_index("ix_registros_jornada_fecha", "registros_jornada", ["fecha"])


def downgrade():
    op.drop_index("ix_registros_jornada_fecha", table_name="registros_jornada")
    op.drop_index("ix_registros_jornada_usuario_id", table_name="registros_jornada")
    op.drop_table("registros_jornada")
    op.drop_column("usuarios", "hora_salida_predeterminada")
    op.drop_column("usuarios", "hora_entrada_predeterminada")
