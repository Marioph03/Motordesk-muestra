"""Añade autorización OAuth de Microsoft a la configuración de correo."""

from alembic import op
import sqlalchemy as sa


revision = "d3e4f5a6b7c8"
down_revision = "d2e3f4a5b6c7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("configuracion_email", sa.Column("microsoft_refresh_token_cifrada", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("configuracion_email", "microsoft_refresh_token_cifrada")
