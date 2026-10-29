"""add ausencias personal

Revision ID: d1a7b8c9e0f1
Revises: 942f77a16513
Create Date: 2026-08-20 12:15:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "d1a7b8c9e0f1"
down_revision = "942f77a16513"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ausencias_personal",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("fecha_inicio", sa.DateTime(), nullable=False),
        sa.Column("fecha_fin", sa.DateTime(), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ausencias_personal_usuario_id",
        "ausencias_personal",
        ["usuario_id"],
    )
    op.create_index(
        "ix_ausencias_personal_tipo",
        "ausencias_personal",
        ["tipo"],
    )
    op.create_index(
        "ix_ausencias_personal_fecha_inicio",
        "ausencias_personal",
        ["fecha_inicio"],
    )
    op.create_index(
        "ix_ausencias_personal_fecha_fin",
        "ausencias_personal",
        ["fecha_fin"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ausencias_personal_fecha_fin",
        table_name="ausencias_personal",
    )
    op.drop_index(
        "ix_ausencias_personal_fecha_inicio",
        table_name="ausencias_personal",
    )
    op.drop_index(
        "ix_ausencias_personal_tipo",
        table_name="ausencias_personal",
    )
    op.drop_index(
        "ix_ausencias_personal_usuario_id",
        table_name="ausencias_personal",
    )
    op.drop_table("ausencias_personal")
