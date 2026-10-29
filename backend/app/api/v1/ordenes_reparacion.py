"""Endpoints del ciclo de órdenes, presupuestos y garantías."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.orden_reparacion import (
    OrdenReparacionCreate,
    OrdenReparacionResponse,
    OrdenReparacionUpdate
)

from app.schemas.estado_orden import EstadoOrdenUpdate
from app.schemas.pagination import PaginationParams
from app.schemas.paginated_response import PaginatedResponse
from app.schemas.garantia import GarantiaResolverRequest

from app.services.orden_reparacion_service import OrdenReparacionService
from app.services.pdf_service import PdfService

from app.core.security import get_current_user
from app.core.permissions import require_permission
from app.models.usuario import Usuario


router = APIRouter(
    prefix="/ordenes-reparacion",
    tags=["Órdenes de Reparación"],
    dependencies=[Depends(get_current_user)]
)


# =========================================================
# LISTADO PAGINADO
# =========================================================

@router.get(
    "/",
    response_model=PaginatedResponse[OrdenReparacionResponse]
)
def get_ordenes(
    pagination: PaginationParams = Depends(),
    tipo: str | None = Query(default=None, pattern="^(OR|PR|GA)$"),
    estado: str | None = Query(default=None),
    db: Session = Depends(get_db)
):

    return OrdenReparacionService.get_paginated(
        db,
        pagination,
        tipo,
        estado,
    )


# =========================================================
# BUSCAR ÓRDENES
# IMPORTANTE: debe estar antes de /{orden_id}
# =========================================================

@router.get(
    "/buscar",
    response_model=list[OrdenReparacionResponse]
)
def buscar_ordenes(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):

    return OrdenReparacionService.buscar(
        db,
        q
    )


# =========================================================
# GENERAR PDF DE LA ORDEN
# IMPORTANTE: también antes de /{orden_id}
# =========================================================

@router.get("/{orden_id}/pdf")
def generar_pdf_orden(
    orden_id: int,
    db: Session = Depends(get_db)
):
    try:

        pdf_buffer = OrdenReparacionService.generar_pdf(
            db,
            orden_id
        )

        orden = OrdenReparacionService.get_by_id(db, orden_id)
        prefijo = "presupuesto" if orden.tipo == "PR" else "orden"
        nombre_archivo = f"{prefijo}_{orden.numero}.pdf"

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    f'inline; filename="{nombre_archivo}"'
            }
        )

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Error generando PDF: {str(e)}"
        )

# =========================================================
# ENVIAR ORDEN POR EMAIL
# =========================================================

@router.post("/{orden_id}/enviar-email")
def enviar_orden_email(
    orden_id: int,
    db: Session = Depends(get_db)
):
    try:

        return OrdenReparacionService.enviar_email(
            db,
            orden_id
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except RuntimeError as e:

        raise HTTPException(
            status_code=502,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Error enviando la orden por email: {str(e)}"
        )


@router.post("/{orden_id}/enviar-whatsapp")
def enviar_orden_whatsapp(
    orden_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:

        if current_user.empresa_id is None:
            raise HTTPException(
                status_code=403,
                detail="El usuario autenticado no tiene una empresa asignada.",
            )

        return OrdenReparacionService.enviar_whatsapp(
            db=db,
            orden_id=orden_id,
            empresa_id=current_user.empresa_id,
        )

    except HTTPException:
        raise

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except RuntimeError as e:

        raise HTTPException(
            status_code=502,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error enviando la orden por WhatsApp: "
                f"{str(e)}"
            )
        )
        
# =========================================================
# ACCIONES DE GARANTÍA
# =========================================================

@router.post("/{orden_id}/crear-garantia", response_model=OrdenReparacionResponse, status_code=201)
def crear_garantia_desde_orden(orden_id: int, db: Session = Depends(get_db)):
    try:
        return OrdenReparacionService.crear_garantia_desde_orden(db, orden_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/garantias/desde-factura/{factura_id}", response_model=OrdenReparacionResponse, status_code=201)
def crear_garantia_desde_factura(factura_id: int, db: Session = Depends(get_db)):
    try:
        return OrdenReparacionService.crear_garantia_desde_factura(db, factura_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

def _ejecutar_accion_garantia(accion, garantia_id: int, db: Session):
    try:
        return accion(db, garantia_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{garantia_id}/garantia/iniciar-revision", response_model=OrdenReparacionResponse)
def iniciar_revision_garantia(garantia_id: int, db: Session = Depends(get_db)):
    return _ejecutar_accion_garantia(
        OrdenReparacionService.iniciar_revision_garantia, garantia_id, db
    )


@router.post("/{garantia_id}/garantia/aprobar", response_model=OrdenReparacionResponse)
def aprobar_garantia(garantia_id: int, db: Session = Depends(get_db)):
    return _ejecutar_accion_garantia(
        OrdenReparacionService.aprobar_garantia, garantia_id, db
    )


@router.post("/{garantia_id}/garantia/rechazar", response_model=OrdenReparacionResponse)
def rechazar_garantia(garantia_id: int, db: Session = Depends(get_db)):
    return _ejecutar_accion_garantia(
        OrdenReparacionService.rechazar_garantia, garantia_id, db
    )


@router.post("/{garantia_id}/garantia/iniciar-reparacion", response_model=OrdenReparacionResponse)
def iniciar_reparacion_garantia(garantia_id: int, db: Session = Depends(get_db)):
    return _ejecutar_accion_garantia(
        OrdenReparacionService.iniciar_reparacion_garantia, garantia_id, db
    )


@router.post("/{garantia_id}/garantia/resolver", response_model=OrdenReparacionResponse)
def resolver_garantia(
    garantia_id: int,
    datos: GarantiaResolverRequest,
    db: Session = Depends(get_db)
):
    try:
        return OrdenReparacionService.resolver_garantia(
            db, garantia_id, datos.resolucion
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================
# OBTENER ORDEN GENERADA DESDE UN PRESUPUESTO
# Debe declararse antes de /{orden_id}.
# =========================================================

@router.get(
    "/{presupuesto_id}/orden-generada",
    response_model=OrdenReparacionResponse
)
def get_orden_generada_desde_presupuesto(
    presupuesto_id: int,
    db: Session = Depends(get_db)
):
    try:
        return OrdenReparacionService.get_orden_generada_desde_presupuesto(
            db,
            presupuesto_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# =========================================================
# OBTENER ORDEN POR ID
# =========================================================

@router.get(
    "/{orden_id}",
    response_model=OrdenReparacionResponse
)
def get_orden(
    orden_id: int,
    db: Session = Depends(get_db)
):
    try:

        return OrdenReparacionService.get_by_id(
            db,
            orden_id
        )

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

# =========================================================
# CREAR ORDEN
# =========================================================

@router.post(
    "/",
    response_model=OrdenReparacionResponse,
    status_code=201
)
def create_orden(
    orden: OrdenReparacionCreate,
    db: Session = Depends(get_db)
):

    try:

        return OrdenReparacionService.create(
            db,
            orden
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# =========================================================
# CAMBIAR ESTADO
# =========================================================

@router.patch(
    "/{orden_id}/estado",
    response_model=OrdenReparacionResponse
)
def cambiar_estado(
    orden_id: int,
    datos: EstadoOrdenUpdate,
    db: Session = Depends(get_db)
):

    try:

        return OrdenReparacionService.cambiar_estado(
            db,
            orden_id,
            datos.estado
        )

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@router.post("/{orden_id}/anular", response_model=OrdenReparacionResponse)
def anular_orden(
    orden_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("ordenes.editar")),
):
    try:
        return OrdenReparacionService.anular(db, orden_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# =========================================================
# ACTUALIZAR ORDEN
# =========================================================

@router.patch(
    "/{orden_id}",
    response_model=OrdenReparacionResponse
)
def actualizar_orden(
    orden_id: int,
    datos: OrdenReparacionUpdate,
    db: Session = Depends(get_db)
):

    try:

        return OrdenReparacionService.update(
            db,
            orden_id,
            datos
        )

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


# =========================================================
# ELIMINAR ORDEN
# =========================================================

@router.delete(
    "/{orden_id}",
    status_code=204
)
def eliminar_orden(
    orden_id: int,
    db: Session = Depends(get_db)
):

    try:

        OrdenReparacionService.delete(
            db,
            orden_id
        )

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
        
@router.post(
    "/{presupuesto_id}/convertir-en-orden",
    response_model=OrdenReparacionResponse
)
def convertir_presupuesto_en_orden(
    presupuesto_id: int,
    db: Session = Depends(get_db)
):

    try:

        return (
            OrdenReparacionService
            .convertir_presupuesto_en_orden(
                db,
                presupuesto_id
            )
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post(
    "/{presupuesto_id}/enviar",
    response_model=OrdenReparacionResponse,
)
def enviar_presupuesto(
    presupuesto_id: int,
    db: Session = Depends(get_db),
):
    try:
        return OrdenReparacionService.enviar_presupuesto(db, presupuesto_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{presupuesto_id}/aceptar",
    response_model=OrdenReparacionResponse,
)
def aceptar_presupuesto(
    presupuesto_id: int,
    db: Session = Depends(get_db),
):
    try:
        return OrdenReparacionService.aceptar_presupuesto(db, presupuesto_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{presupuesto_id}/rechazar",
    response_model=OrdenReparacionResponse,
)
def rechazar_presupuesto(
    presupuesto_id: int,
    db: Session = Depends(get_db),
):
    try:
        return OrdenReparacionService.rechazar_presupuesto(db, presupuesto_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
