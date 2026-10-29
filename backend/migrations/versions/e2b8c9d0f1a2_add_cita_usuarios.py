"""add cita usuarios

Revision ID: e2b8c9d0f1a2
Revises: d1a7b8c9e0f1
Create Date: 2026-08-21 10:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "e2b8c9d0f1a2"
down_revision = "d1a7b8c9e0f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cita_usuarios",
        sa.Column("cita_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["cita_id"],
            ["citas.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("cita_id", "usuario_id"),
    )


def downgrade() -> None:
    op.drop_table("cita_usuarios")
