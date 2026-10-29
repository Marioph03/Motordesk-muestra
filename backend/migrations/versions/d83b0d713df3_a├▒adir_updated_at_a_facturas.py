"""Añadir updated_at a facturas"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d83b0d713df3"
down_revision: Union[str, Sequence[str], None] = "99ae3a86b429"
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.add_column(
        "facturas",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now()
        )
    )

    op.alter_column(
        "facturas",
        "updated_at",
        server_default=None
    )


def downgrade() -> None:

    op.drop_column(
        "facturas",
        "updated_at"
    )