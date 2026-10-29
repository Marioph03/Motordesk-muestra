"""Añade autorización OAuth de Google a la configuración de correo."""

from alembic import op
import sqlalchemy as sa

revision = "d2e3f4a5b6c7"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("configuracion_email", sa.Column("metodo_autenticacion", sa.String(length=30), nullable=False, server_default="password"))
    op.add_column("configuracion_email", sa.Column("google_refresh_token_cifrada", sa.Text(), nullable=True))
    op.alter_column("configuracion_email", "password_cifrada", existing_type=sa.Text(), nullable=True)


def downgrade():
    op.alter_column("configuracion_email", "password_cifrada", existing_type=sa.Text(), nullable=False)
    op.drop_column("configuracion_email", "google_refresh_token_cifrada")
    op.drop_column("configuracion_email", "metodo_autenticacion")
