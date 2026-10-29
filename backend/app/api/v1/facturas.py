"""Endpoints de facturación y acceso a documentos fiscales."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from app.core.security import get_current_user
from app.core.permissions import require_permission
from app.database.database import get_db
from app.models.usuario import Usuario
from app.schemas.factura import (
    FacturaCreate,
    FacturaDesdeAlbaranesVentaCreate,
    FacturaDesdeOrdenesCreate,
    FacturaUpdate,
    FacturaResponse
)
from app.services.factura_service import FacturaService
from app.schemas.factura_filtro import FacturaFiltro
from app.schemas.pagination import PaginationParams
from app.schemas.paginated_response import PaginatedResponse
from app.schemas.registro_verifactu import RegistroVerifactuResponse
from app.services.verifactu_service import VerifactuService
from app.schemas.facturae import FacturaeDestinoResponse, FacturaeDestinoUpdate
from app.services.facturae_service import FacturaeService
from app.schemas.facturae_organismo import FacturaeOrganismoResponse, FacturaeOrganismoUpdate
from app.services.facturae_organismo_service import FacturaeOrganismoService


router = APIRouter(
    prefix="/facturas",
    tags=["Facturas"],
    dependencies=[Depends(get_current_user)]
)


def _empresa_id(usuario: Usuario) -> int:
    if usuario.empresa_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El usuario no tiene una empresa asignada")
    return usuario.empresa_id


@router.get("/", response_model=PaginatedResponse[FacturaResponse])
def get_facturas(
    pagination: PaginationParams = Depends(),
    filtros: FacturaFiltro = Depends(),
    db: Session = Depends(get_db)
):
    return FacturaService.get_paginated(
        db,
        pagination,
        filtros,
    )


@router.get(
    "/orden/{orden_id}",
    response_model=FacturaResponse
)
def get_factura_por_orden(
    orden_id: int,
    db: Session = Depends(get_db)
):
    try:
        return FacturaService.get_by_orden(
            db,
            orden_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/facturae-organismos", response_model=list[FacturaeOrganismoResponse])
def listar_organismos_facturae(
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("facturas.emitir")),
):
    return FacturaeOrganismoService.listar(db, _empresa_id(usuario), q)


@router.post("/facturae-organismos", response_model=FacturaeOrganismoResponse, status_code=status.HTTP_201_CREATED)
def crear_organismo_facturae(
    datos: FacturaeOrganismoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("facturas.emitir")),
):
    return FacturaeOrganismoService.guardar(db, _empresa_id(usuario), datos)


@router.put("/facturae-organismos/{organismo_id}", response_model=FacturaeOrganismoResponse)
def actualizar_organismo_facturae(
    organismo_id: int,
    datos: FacturaeOrganismoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("facturas.emitir")),
):
    try:
        return FacturaeOrganismoService.guardar(db, _empresa_id(usuario), datos, organismo_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post(
    "/desde-orden/{orden_id}",
    response_model=FacturaResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_factura_desde_orden(
    orden_id: int,
    tipo_documento: str,
    cliente_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        return FacturaService.crear_desde_orden(
            db,
            orden_id,
            tipo_documento,
            cliente_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

@router.post("/desde-ordenes", response_model=FacturaResponse, status_code=status.HTTP_201_CREATED)
def crear_factura_desde_ordenes(datos: FacturaDesdeOrdenesCreate, db: Session = Depends(get_db), _: Usuario = Depends(require_permission("facturas.crear"))):
    try:
        return FacturaService.crear_desde_ordenes(db, datos.ordenes_ids, datos.tipo_documento, datos.cliente_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/desde-garantia/{garantia_id}",
    response_model=FacturaResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_factura_desde_garantia(
    garantia_id: int,
    db: Session = Depends(get_db),
):
    try:
        return FacturaService.crear_desde_garantia(db, garantia_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/desde-albaran-venta/{albaran_venta_id}",
    response_model=FacturaResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_factura_desde_albaran_venta(
    albaran_venta_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("facturas.crear")),
):
    try:
        return FacturaService.crear_desde_albaran_venta(
            db,
            albaran_venta_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/desde-albaranes-venta",
    response_model=FacturaResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_factura_desde_albaranes_venta(
    datos: FacturaDesdeAlbaranesVentaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("facturas.crear")),
):
    try:
        return FacturaService.crear_desde_albaranes_venta(
            db,
            datos.albaranes_venta_ids,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{factura_id}", response_model=FacturaResponse)
def get_factura(
    factura_id: int,
    db: Session = Depends(get_db)
):
    try:
        return FacturaService.get_by_id(
            db,
            factura_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{factura_id}/facturae-destino", response_model=FacturaeDestinoResponse)
def obtener_destino_facturae(factura_id: int, db: Session = Depends(get_db)):
    destino = FacturaeService.obtener_destino(db, factura_id)
    if destino is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Esta factura no tiene datos Facturae")
    return destino


@router.put("/{factura_id}/facturae-destino", response_model=FacturaeDestinoResponse)
def guardar_destino_facturae(
    factura_id: int,
    datos: FacturaeDestinoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("facturas.emitir")),
):
    try:
        return FacturaeService.guardar_destino(db, factura_id, datos)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/",
    response_model=FacturaResponse,
    status_code=status.HTTP_201_CREATED
)
def create_factura(
    factura: FacturaCreate,
    db: Session = Depends(get_db)
):
    try:
        return FacturaService.create(
            db,
            factura
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{factura_id}", response_model=FacturaResponse)
def update_factura(
    factura_id: int,
    datos: FacturaUpdate,
    db: Session = Depends(get_db)
):
    try:
        return FacturaService.update(
            db,
            factura_id,
            datos
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{factura_id}")
def delete_factura(
    factura_id: int,
    db: Session = Depends(get_db)
):
    try:
        FacturaService.delete(
            db,
            factura_id
        )

        return {
            "mensaje": "Factura eliminada correctamente"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{factura_id}/emitir",
    response_model=FacturaResponse
)
def emitir_factura(
    factura_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("facturas.emitir")
    ),
):
    try:
        if usuario.empresa_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario autenticado no tiene una empresa asignada.",
            )
        return FacturaService.emitir(
            db,
            factura_id,
            usuario.empresa_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{factura_id}/anular",
    response_model=FacturaResponse
)
def anular_factura(
    factura_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("facturas.anular")
    ),
):
    try:
        return FacturaService.anular(
            db,
            factura_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{factura_id}/enviar-email")
def enviar_factura_email(
    factura_id: int,
    db: Session = Depends(get_db)
):
    try:
        return FacturaService.enviar_email(db, factura_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enviando la factura por email: {str(e)}"
        )


@router.post("/{factura_id}/enviar-whatsapp")
def enviar_factura_whatsapp(
    factura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        if current_user.empresa_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario autenticado no tiene una empresa asignada.",
            )

        return FacturaService.enviar_whatsapp(
            db=db,
            factura_id=factura_id,
            empresa_id=current_user.empresa_id,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enviando la factura por WhatsApp: {str(e)}"
        )


@router.get(
    "/{factura_id}/pdf"
)
def descargar_pdf(
    factura_id: int,
    db: Session = Depends(get_db)
):

    try:

        pdf = FacturaService.generar_pdf(
            db,
            factura_id
        )

        return StreamingResponse(
            pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                f'attachment; filename="factura_{factura_id}.pdf"'
            }
        )

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
        
@router.get(
    "/buscar",
    response_model=list[FacturaResponse]
)
def buscar_facturas(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    return FacturaService.buscar(
        db,
        q
    )
    
@router.get(
    "/filtrar",
    response_model=list[FacturaResponse]
)
def filtrar_facturas(
    filtros: FacturaFiltro = Depends(),
    db: Session = Depends(get_db)
):
    return FacturaService.filtrar(
        db,
        filtros
    )
    
@router.post(
    "/{factura_id}/actualizar-desde-orden",
    response_model=FacturaResponse
)
def actualizar_desde_orden(
    factura_id: int,
    db: Session = Depends(get_db)
):

    try:

        return FacturaService.actualizar_desde_orden(
            db,
            factura_id
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
