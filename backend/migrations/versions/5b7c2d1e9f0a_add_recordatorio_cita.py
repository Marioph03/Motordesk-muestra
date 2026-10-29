"""add recordatorio cita"""
from alembic import op
import sqlalchemy as sa
revision = "5b7c2d1e9f0a"
down_revision = "4a8e19c2d0f1"
branch_labels = None
depends_on = None
def upgrade():
    op.add_column("citas", sa.Column("fecha_recordatorio", sa.DateTime(), nullable=True))
    op.add_column("citas", sa.Column("canal_recordatorio", sa.String(length=20), nullable=True))
def downgrade():
    op.drop_column("citas", "canal_recordatorio")
    op.drop_column("citas", "fecha_recordatorio")
