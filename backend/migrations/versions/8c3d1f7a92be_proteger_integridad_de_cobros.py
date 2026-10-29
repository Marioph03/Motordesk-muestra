"""proteger integridad de cobros

Revision ID: 8c3d1f7a92be
Revises: 05b0d9e0c6f9
Create Date: 2026-08-07
"""

from typing import Sequence, Union

from alembic import op


revision: str = "8c3d1f7a92be"
down_revision: Union[str, Sequence[str], None] = "05b0d9e0c6f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_pagos_factura_importe_positivo",
        "pagos_factura",
        "importe > 0"
    )
    op.create_check_constraint(
        "ck_pagos_factura_metodo_pago_valido",
        "pagos_factura",
        "metodo_pago IN ('EFECTIVO', 'TARJETA', 'TRANSFERENCIA', 'BIZUM', 'OTRO')"
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_pagos_factura_metodo_pago_valido",
        "pagos_factura",
        type_="check"
    )
    op.drop_constraint(
        "ck_pagos_factura_importe_positivo",
        "pagos_factura",
        type_="check"
    )
