"""Agrega la clasificacion de los proveedores."""

from alembic import op
import sqlalchemy as sa


revision = "fae013"
down_revision = "fae012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "proveedores",
        sa.Column(
            "tipo",
            sa.String(length=30),
            nullable=False,
            server_default="COMPRA",
        ),
    )


def downgrade() -> None:
    op.drop_column("proveedores", "tipo")
