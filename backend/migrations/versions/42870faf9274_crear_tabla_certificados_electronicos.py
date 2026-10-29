"""crear tabla certificados electronicos

Revision ID: 42870faf9274
Revises: 8e34025998d9
Create Date: 2026-09-11 12:30:45.298358
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "42870faf9274"
down_revision: Union[str, Sequence[str], None] = "8e34025998d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "certificados_electronicos",

        sa.Column("id", sa.Integer(), nullable=False ),
        sa.Column("empresa_id", sa.Integer(), nullable=False ),
        sa.Column("nombre_archivo", sa.String(length=255), nullable=False ),
        sa.Column("ruta_archivo", sa.String(length=500), nullable=False ),
        sa.Column("password_cifrada", sa.Text(), nullable=False ),
        sa.Column("titular", sa.String(length=255), nullable=True ),
        sa.Column("nif_titular", sa.String(length=20), nullable=True ),
        sa.Column("emisor", sa.String(length=255), nullable=True ),
        sa.Column("fecha_validez_desde", sa.DateTime(), nullable=True ),
        sa.Column("fecha_caducidad", sa.DateTime(), nullable=True ),
        sa.Column("activo", sa.Boolean(), nullable=False ),
        sa.Column("created_at", sa.DateTime(), nullable=False ),
        sa.Column("updated_at", sa.DateTime(), nullable=False ),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresa.id"], ondelete="CASCADE" ),
        sa.PrimaryKeyConstraint("id")
    )

    op.create_index(
        op.f("ix_certificados_electronicos_id"),
        "certificados_electronicos",
        ["id"],
        unique=False
    )

    op.create_index(
        op.f("ix_certificados_electronicos_empresa_id"),
        "certificados_electronicos",
        ["empresa_id"],
        unique=True
    )


def downgrade() -> None:

    op.drop_index(
        op.f("ix_certificados_electronicos_empresa_id"),
        table_name="certificados_electronicos"
    )

    op.drop_index(
        op.f("ix_certificados_electronicos_id"),
        table_name="certificados_electronicos"
    )

    op.drop_table(
        "certificados_electronicos"
    )