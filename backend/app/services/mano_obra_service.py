from decimal import Decimal
from sqlalchemy.orm import Session

from app.repositories.mano_obra_repository import ManoObraRepository
from app.repositories.orden_reparacion_repository import OrdenReparacionRepository
from app.models.orden_reparacion import EstadoReparacion
from app.schemas.mano_obra import ManoObraCreate, ManoObraUpdate

from app.schemas.mano_obra import ManoObraResponse
from app.schemas.paginated_response import PaginatedResponse
from app.schemas.pagination import PaginationParams
from app.services.orden_reparacion_service import OrdenReparacionService

class ManoObraService:

    @staticmethod
    def _calcular_importe_sin_iva(
        horas: Decimal,
        precio_hora: Decimal,
        descuento_porcentaje: Decimal,
    ) -> Decimal:
        """Calcula mano de obra con descuento, siempre antes de IVA."""
        importe_bruto = horas * precio_hora
        return importe_bruto * (
            Decimal("1") - descuento_porcentaje / Decimal("100")
        )

    @staticmethod
    def _normalizar_codigo_mano_obra(orden, codigo: str | None) -> str | None:
        """Permite códigos de operación únicamente en órdenes de garantía."""
        if codigo is None:
            return None

        if orden.tipo != "GA":
            raise ValueError(
                "El código de mano de obra solo puede indicarse en una garantía"
            )

        return codigo

    @staticmethod
    def _validar_orden_editable(orden) -> None:
        if orden.tipo == "PR" and orden.estado != EstadoReparacion.BORRADOR.value:
            raise ValueError("No se puede modificar la mano de obra de un presupuesto que no está en borrador")

    @staticmethod
    def get_by_orden(db: Session, orden_id: int):

        orden = OrdenReparacionRepository.get_by_id(db, orden_id)

        if orden is None:
            raise ValueError("La orden de reparación no existe")

        return ManoObraRepository.get_by_orden(db, orden_id)

    @staticmethod
    def create(
        db: Session,
        orden_id: int,
        mano_obra: ManoObraCreate
    ):

        orden = OrdenReparacionRepository.get_by_id(db, orden_id)

        if orden is None:
            raise ValueError("La orden de reparación no existe")

        ManoObraService._validar_orden_editable(orden)

        codigo_mano_obra = ManoObraService._normalizar_codigo_mano_obra(
            orden,
            mano_obra.codigo_mano_obra,
        )

        total = ManoObraService._calcular_importe_sin_iva(
            mano_obra.horas,
            mano_obra.precio_hora,
            mano_obra.descuento_porcentaje,
        )

        datos = {
            "concepto": mano_obra.concepto,
            "codigo_mano_obra": codigo_mano_obra,
            "horas": mano_obra.horas,
            "precio_hora": mano_obra.precio_hora,
            "descuento_porcentaje": mano_obra.descuento_porcentaje,
            "cubierto_garantia": mano_obra.cubierto_garantia,
            "total": total
        }

        nueva = ManoObraRepository.create(
            db,
            orden_id,
            datos
        )
        OrdenReparacionService.recalcular_totales(db, orden_id)
        return nueva
        
    @staticmethod
    def update(
        db: Session,
        linea_id: int,
        datos: ManoObraUpdate
    ):
        linea = ManoObraRepository.get_by_id(db, linea_id)

        if linea is None:
            raise ValueError("La línea de mano de obra no existe")

        orden = OrdenReparacionRepository.get_by_id(db, linea.orden_id)
        if orden is None:
            raise ValueError("La orden de reparación no existe")
        ManoObraService._validar_orden_editable(orden)

        datos_actualizados = datos.model_dump(exclude_unset=True)

        if "codigo_mano_obra" in datos_actualizados:
            datos_actualizados["codigo_mano_obra"] = (
                ManoObraService._normalizar_codigo_mano_obra(
                    orden,
                    datos_actualizados["codigo_mano_obra"],
                )
            )

        if (
            "horas" in datos_actualizados
            or "precio_hora" in datos_actualizados
            or "descuento_porcentaje" in datos_actualizados
        ):
            horas = datos_actualizados.get(
    "horas",
    linea.horas
)

        precio = datos_actualizados.get(
            "precio_hora",
            linea.precio_hora
        )

        descuento = datos_actualizados.get(
            "descuento_porcentaje",
            linea.descuento_porcentaje
        )

        datos_actualizados["total"] = (
            ManoObraService._calcular_importe_sin_iva(
                horas,
                precio,
                descuento,
            )
        )

        linea = ManoObraRepository.update(
            db,
            linea,
            datos_actualizados
        )
        OrdenReparacionService.recalcular_totales(db, linea.orden_id)
        return linea
        
    @staticmethod
    def delete(
        db: Session,
        linea_id: int
    ):
        linea = ManoObraRepository.get_by_id(
            db,
            linea_id
        )

        if linea is None:
            raise ValueError(
                "La línea de mano de obra no existe"
            )

        orden = OrdenReparacionRepository.get_by_id(db, linea.orden_id)
        if orden is None:
            raise ValueError("La orden de reparación no existe")
        ManoObraService._validar_orden_editable(orden)

        ManoObraRepository.delete(
            db,
            linea
        )
        OrdenReparacionService.recalcular_totales(db, orden.id)
        
    @staticmethod
    def get_paginated(
        db: Session,
        pagination: PaginationParams
    ):
        items, total = ManoObraRepository.get_paginated(
            db,
            pagination
        )

        return PaginatedResponse[ManoObraResponse].create(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size
        )
"""Reglas de mano de obra de órdenes y actualización de sus importes."""
