from sqlalchemy.orm import Session

from app.models.actividad import Actividad

from app.schemas.actividad import (
    ActividadCreate,
    ActividadResponse
)

from app.schemas.pagination import PaginationParams
from app.schemas.paginated_response import PaginatedResponse
from app.schemas.actividad_filtro import ActividadFiltro
from sqlalchemy.orm import joinedload


class ActividadService:

    @staticmethod
    def registrar_evento(
        db: Session,
        *,
        empresa_id: int | None,
        usuario_id: int,
        modulo: str,
        accion: str,
        descripcion: str,
        registro_id: int | None = None,
        ip: str | None = None,
    ) -> Actividad | None:
        """Registra un evento sin hacer fallar la operación ya realizada."""
        if empresa_id is None:
            return None

        actividad = Actividad(
            empresa_id=empresa_id,
            usuario_id=usuario_id,
            modulo=modulo,
            accion=accion,
            registro_id=registro_id,
            descripcion=descripcion,
            ip=ip,
        )
        db.add(actividad)
        db.commit()
        db.refresh(actividad)
        return actividad

    # =====================================================
    # REGISTRAR ACTIVIDAD
    # =====================================================

    @staticmethod
    def registrar(
        db: Session,
        datos: ActividadCreate
    ) -> Actividad:

        actividad = Actividad(
            empresa_id=datos.empresa_id,
            usuario_id=datos.usuario_id,
            modulo=datos.modulo,
            accion=datos.accion,
            registro_id=datos.registro_id,
            descripcion=datos.descripcion,
            ip=datos.ip
        )

        db.add(actividad)

        db.commit()

        db.refresh(actividad)

        return actividad

    # =====================================================
    # LISTADO PAGINADO
    # =====================================================

    @staticmethod
    def get_paginated(
        db: Session,
        pagination: PaginationParams
    ) -> PaginatedResponse[ActividadResponse]:

        query = (
        db.query(Actividad)
        .options(
        joinedload(Actividad.usuario)
        )
        )

        total = query.count()

        actividades = (
            query
            .order_by(
                Actividad.created_at.desc()
            )
            .offset(pagination.skip)
            .limit(pagination.size)
            .all()
        )

        return PaginatedResponse[ActividadResponse].create(
            items=actividades,
            total=total,
            page=pagination.page,
            size=pagination.size
        )

    # =====================================================
    # OBTENER POR ID
    # =====================================================

    @staticmethod
    def get_by_id(
        db: Session,
        actividad_id: int
    ) -> Actividad:

        actividad = (
            db.query(Actividad)
            .options(
                joinedload(Actividad.usuario)
            )
            .filter(
                Actividad.id == actividad_id
            )
            .first()
        )

        if actividad is None:

            raise ValueError(
                "Actividad no encontrada"
            )

        return actividad
    
    # =====================================================
# LISTADO PAGINADO
# =====================================================

    @staticmethod
    def get_paginated(
        db: Session,
        pagination: PaginationParams,
        filtro: ActividadFiltro | None = None
    ) -> PaginatedResponse[ActividadResponse]:

        query = db.query(Actividad)

    # =====================================================
    # FILTROS
    # =====================================================

        if filtro:

            if filtro.usuario_id is not None:
                query = query.filter(
                    Actividad.usuario_id == filtro.usuario_id
                )

            if filtro.modulo:
                query = query.filter(
                    Actividad.modulo == filtro.modulo
                )

            if filtro.accion:
                query = query.filter(
                    Actividad.accion == filtro.accion
                )

            if filtro.fecha_desde:
                query = query.filter(
                    Actividad.created_at >= filtro.fecha_desde
                )

            if filtro.fecha_hasta:
                query = query.filter(
                    Actividad.created_at <= filtro.fecha_hasta
                )

    # =====================================================
    # PAGINACIÓN
    # =====================================================

        total = query.count()

        actividades = (
        query
        .order_by(Actividad.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.size)
        .all()
        )

        return PaginatedResponse[ActividadResponse].create(
            items=actividades,
            total=total,
            page=pagination.page,
            size=pagination.size
        )
