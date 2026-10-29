"""permitir facturas manuales sin orden

Revision ID: e14b8a9d2c71
Revises: d00e6bed6e89
Create Date: 2026-08-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e14b8a9d2c71"
down_revision: Union[str, Sequence[str], None] = "d00e6bed6e89"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "facturas",
        "orden_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    # No se puede volver a imponer NOT NULL de forma segura mientras existan
    # facturas manuales sin orden asociada.
    op.alter_column(
        "facturas",
        "orden_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
