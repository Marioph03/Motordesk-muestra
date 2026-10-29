"""add whatsapp integration to empresa

Revision ID: 15d44f962230
Revises: 915c9031a0af
Create Date: 2026-07-31 11:48:23.695805

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "15d44f962230"

down_revision: Union[
    str,
    Sequence[str],
    None
] = "915c9031a0af"

branch_labels: Union[
    str,
    Sequence[str],
    None
] = None

depends_on: Union[
    str,
    Sequence[str],
    None
] = None


def upgrade() -> None:
    """Añade la integración de WhatsApp a empresa."""

    # =========================================================
    # ESTADO DE CONEXIÓN
    # =========================================================

    op.add_column(
        "empresa",
        sa.Column(
            "whatsapp_conectado",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false()
        )
    )


    # =========================================================
    # WHATSAPP BUSINESS ACCOUNT
    # =========================================================

    op.add_column(
        "empresa",
        sa.Column(
            "whatsapp_waba_id",
            sa.String(length=100),
            nullable=True
        )
    )


    # =========================================================
    # PHONE NUMBER ID
    # =========================================================

    op.add_column(
        "empresa",
        sa.Column(
            "whatsapp_phone_number_id",
            sa.String(length=100),
            nullable=True
        )
    )


    # =========================================================
    # ACCESS TOKEN
    # =========================================================

    op.add_column(
        "empresa",
        sa.Column(
            "whatsapp_access_token",
            sa.Text(),
            nullable=True
        )
    )


    # =========================================================
    # ELIMINAR DEFAULT DE POSTGRESQL
    # =========================================================

    op.alter_column(
        "empresa",
        "whatsapp_conectado",
        server_default=None
    )


def downgrade() -> None:
    """Elimina la integración de WhatsApp de empresa."""

    op.drop_column(
        "empresa",
        "whatsapp_access_token"
    )

    op.drop_column(
        "empresa",
        "whatsapp_phone_number_id"
    )

    op.drop_column(
        "empresa",
        "whatsapp_waba_id"
    )

    op.drop_column(
        "empresa",
        "whatsapp_conectado"
    )