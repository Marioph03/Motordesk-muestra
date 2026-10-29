"""Allow one spare-parts invoice to include multiple sales delivery notes.

Revision ID: c4f8a2d9b713
Revises: b8d2e5f7a901
Create Date: 2026-09-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4f8a2d9b713"
down_revision: Union[str, Sequence[str], None] = "b8d2e5f7a901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "facturas_albaranes_venta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("factura_id", sa.Integer(), nullable=False),
        sa.Column("albaran_venta_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["factura_id"],
            ["facturas.id"],
            name="fk_facturas_albaranes_venta_factura_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["albaran_venta_id"],
            ["albaranes_venta.id"],
            name="fk_facturas_albaranes_venta_albaran_venta_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "factura_id",
            "albaran_venta_id",
            name="uq_factura_albaran_venta",
        ),
        sa.UniqueConstraint(
            "albaran_venta_id",
            name="uq_albaran_venta_factura",
        ),
    )
    op.create_index(
        op.f("ix_facturas_albaranes_venta_factura_id"),
        "facturas_albaranes_venta",
        ["factura_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_facturas_albaranes_venta_albaran_venta_id"),
        "facturas_albaranes_venta",
        ["albaran_venta_id"],
        unique=False,
    )

    op.add_column(
        "factura_lineas",
        sa.Column("albaran_venta_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_factura_lineas_albaran_venta_id",
        "factura_lineas",
        "albaranes_venta",
        ["albaran_venta_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_factura_lineas_albaran_venta_id"),
        "factura_lineas",
        ["albaran_venta_id"],
        unique=False,
    )

    # Conserva las facturas creadas por la primera versión de albaranes de
    # venta, que solo permitía un albarán por factura.
    op.execute(
        """
        INSERT INTO facturas_albaranes_venta (factura_id, albaran_venta_id)
        SELECT id, albaran_venta_id
        FROM facturas
        WHERE albaran_venta_id IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE factura_lineas AS linea
        SET albaran_venta_id = factura.albaran_venta_id
        FROM facturas AS factura
        WHERE linea.factura_id = factura.id
          AND factura.albaran_venta_id IS NOT NULL
        """
    )

    op.drop_index(op.f("ix_facturas_albaran_venta_id"), table_name="facturas")
    op.drop_constraint("fk_facturas_albaran_venta_id", "facturas", type_="foreignkey")
    op.drop_column("facturas", "albaran_venta_id")


def downgrade() -> None:
    op.add_column(
        "facturas",
        sa.Column("albaran_venta_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_facturas_albaran_venta_id",
        "facturas",
        "albaranes_venta",
        ["albaran_venta_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_facturas_albaran_venta_id"),
        "facturas",
        ["albaran_venta_id"],
        unique=True,
    )
    op.execute(
        """
        UPDATE facturas AS factura
        SET albaran_venta_id = origen.albaran_venta_id
        FROM (
            SELECT DISTINCT ON (factura_id) factura_id, albaran_venta_id
            FROM facturas_albaranes_venta
            ORDER BY factura_id, id
        ) AS origen
        WHERE factura.id = origen.factura_id
        """
    )
    op.drop_index(op.f("ix_factura_lineas_albaran_venta_id"), table_name="factura_lineas")
    op.drop_constraint(
        "fk_factura_lineas_albaran_venta_id",
        "factura_lineas",
        type_="foreignkey",
    )
    op.drop_column("factura_lineas", "albaran_venta_id")
    op.drop_index(
        op.f("ix_facturas_albaranes_venta_albaran_venta_id"),
        table_name="facturas_albaranes_venta",
    )
    op.drop_index(
        op.f("ix_facturas_albaranes_venta_factura_id"),
        table_name="facturas_albaranes_venta",
    )
    op.drop_table("facturas_albaranes_venta")
