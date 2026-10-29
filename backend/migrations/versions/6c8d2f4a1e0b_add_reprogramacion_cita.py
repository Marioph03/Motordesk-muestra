"""add reprogramacion cita"""

from alembic import op
import sqlalchemy as sa


revision = "6c8d2f4a1e0b"
down_revision = "5b7c2d1e9f0a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("citas", sa.Column("fecha_reprogramacion", sa.DateTime(), nullable=True))
    op.add_column("citas", sa.Column("fecha_inicio_anterior", sa.DateTime(), nullable=True))
    op.add_column("citas", sa.Column("fecha_fin_anterior", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("citas", "fecha_fin_anterior")
    op.drop_column("citas", "fecha_inicio_anterior")
    op.drop_column("citas", "fecha_reprogramacion")
