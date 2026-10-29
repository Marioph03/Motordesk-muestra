"""Endpoints del flujo de pedidos de compra y recepción de mercancía."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status
)
from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.permissions import require_permission
from app.models.usuario import Usuario

from app.repositories.pedido_compra_repository import (
    PedidoCompraRepository
)
from app.repositories.empresa_repository import (
    EmpresaRepository
)

from app.schemas.pedido_compra import (
    PedidoCompraCreate,
    PedidoCompraUpdate,
    PedidoCompraResponse,
    LineaPedidoCompraCreate,
    LineaPedidoCompraUpdate,
    LineaPedidoCompraResponse,
    RecepcionPedidoCreate
)

from app.services.pedido_compra_service import (
    PedidoCompraService
)
from app.services.pdf_service import PdfService
from app.services.configuracion_taller_service import ConfiguracionTallerService
from app.services.configuracion_documentos_service import ConfiguracionDocumentosService


router = APIRouter(
    prefix="/pedidos-compra",
    tags=["Pedidos de compra"]
)

@router.get(
    "",
    response_model=list[PedidoCompraResponse]
)
def listar_pedidos(
    db: Session = Depends(get_db)
):

    return (
        PedidoCompraRepository.get_all(
            db
        )
    )


@router.get(
    "/{pedido_id}",
    response_model=PedidoCompraResponse
)
def obtener_pedido(
    pedido_id: int,
    db: Session = Depends(get_db)
):

    pedido = (
        PedidoCompraRepository.get_by_id(
            db,
            pedido_id
        )
    )

    if pedido is None:

        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    return pedido


@router.get(
    "/{pedido_id}/pdf"
)
def generar_pdf_pedido(
    pedido_id: int,
    db: Session = Depends(get_db)
):

    pedido = PedidoCompraRepository.get_by_id(
        db,
        pedido_id
    )

    if pedido is None:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    empresa = EmpresaRepository.get_first(db)

    pdf_buffer = PdfService.generar_pedido_compra(
        pedido,
        empresa,
        ConfiguracionTallerService.obtener(db),
        ConfiguracionDocumentosService.obtener(db),
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'inline; filename="{pedido.numero}.pdf"'
        }
    )

@router.post(
    "",
    response_model=PedidoCompraResponse,
    status_code=status.HTTP_201_CREATED
)
def crear_pedido(
    datos: PedidoCompraCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("compras.crear")
    ),
):

    try:

        return (
            PedidoCompraService.crear_pedido(
                db,
                datos
            )
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.patch(
    "/{pedido_id}",
    response_model=PedidoCompraResponse
)
def actualizar_pedido(
    pedido_id: int,
    datos: PedidoCompraUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("compras.crear")
    ),
):

    try:

        return (
            PedidoCompraService.actualizar_pedido(
                db,
                pedido_id,
                datos
            )
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
@router.post(
    "/{pedido_id}/lineas",
    response_model=LineaPedidoCompraResponse,
    status_code=status.HTTP_201_CREATED
)
def añadir_linea(
    pedido_id: int,
    datos: LineaPedidoCompraCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("compras.crear")
    ),
):

    try:

        return (
            PedidoCompraService.añadir_linea(
                db,
                pedido_id,
                datos
            )
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
@router.patch(
    "/lineas/{linea_id}",
    response_model=LineaPedidoCompraResponse
)
def actualizar_linea(
    linea_id: int,
    datos: LineaPedidoCompraUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("compras.crear")
    ),
):

    try:

        return (
            PedidoCompraService.actualizar_linea(
                db,
                linea_id,
                datos
            )
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
@router.delete(
    "/lineas/{linea_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def eliminar_linea(
    linea_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("compras.crear")
    ),
):

    try:

        PedidoCompraService.eliminar_linea(
            db,
            linea_id
        )

        return Response(
            status_code=status.HTTP_204_NO_CONTENT
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
@router.post(
    "/{pedido_id}/enviar",
    response_model=PedidoCompraResponse
)
def enviar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("compras.crear")
    ),
):

    try:

        return PedidoCompraService.enviar_pedido(
            db,
            pedido_id
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
@router.post(
    "/{pedido_id}/cancelar",
    response_model=PedidoCompraResponse
)
def cancelar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("compras.crear")
    ),
):

    try:

        return PedidoCompraService.cancelar_pedido(
            db,
            pedido_id
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
@router.post(
    "/{pedido_id}/recibir",
    response_model=PedidoCompraResponse
)
def recibir_pedido(
    pedido_id: int,
    datos: RecepcionPedidoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("compras.recibir")
    ),
):

    try:

        return PedidoCompraService.recibir_mercancia(
            db,
            pedido_id,
            datos
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
@router.post(
    "/generar-desde-reposicion",
    response_model=list[
        PedidoCompraResponse
    ]
)
def generar_desde_reposicion(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("compras.crear")
    ),
):

    try:

        return (
            PedidoCompraService
            .generar_pedidos_reposicion(
                db
            )
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
