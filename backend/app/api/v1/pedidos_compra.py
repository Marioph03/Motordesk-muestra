from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.pedido_compra import (
    LineaPedidoCompraCreate,
    LineaPedidoCompraResponse,
    LineaPedidoCompraUpdate,
    PedidoCompraCreate,
    PedidoCompraResponse,
    PedidoCompraUpdate,
    RecepcionPedidoCreate,
)
from app.services.pedido_compra_service import (
    PedidoCompraService,
)


router = APIRouter(
    prefix="/pedidos-compra",
    tags=["Pedidos de compra"],
)


@router.get(
    "/",
    response_model=list[PedidoCompraResponse],
)
def obtener_pedidos(
    db: Session = Depends(get_db),
):
    return PedidoCompraService.obtener_pedidos(db)


@router.post(
    "/",
    response_model=PedidoCompraResponse,
    status_code=201,
)
def crear_pedido(
    datos: PedidoCompraCreate,
    db: Session = Depends(get_db),
):
    try:
        return PedidoCompraService.crear_pedido(db, datos)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get(
    "/{pedido_id}",
    response_model=PedidoCompraResponse,
)
def obtener_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
):
    try:
        return PedidoCompraService.obtener_pedido(
            db,
            pedido_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.patch(
    "/{pedido_id}",
    response_model=PedidoCompraResponse,
)
def actualizar_pedido(
    pedido_id: int,
    datos: PedidoCompraUpdate,
    db: Session = Depends(get_db),
):
    try:
        return PedidoCompraService.actualizar_pedido(
            db,
            pedido_id,
            datos,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.post(
    "/{pedido_id}/lineas",
    response_model=LineaPedidoCompraResponse,
    status_code=201,
)
def anadir_linea(
    pedido_id: int,
    datos: LineaPedidoCompraCreate,
    db: Session = Depends(get_db),
):
    try:
        return PedidoCompraService.añadir_linea(
            db,
            pedido_id,
            datos,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.patch(
    "/lineas/{linea_id}",
    response_model=LineaPedidoCompraResponse,
)
def actualizar_linea(
    linea_id: int,
    datos: LineaPedidoCompraUpdate,
    db: Session = Depends(get_db),
):
    try:
        return PedidoCompraService.actualizar_linea(
            db,
            linea_id,
            datos,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.delete(
    "/lineas/{linea_id}",
    status_code=204,
)
def eliminar_linea(
    linea_id: int,
    db: Session = Depends(get_db),
):
    try:
        PedidoCompraService.eliminar_linea(
            db,
            linea_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.post(
    "/{pedido_id}/enviar",
    response_model=PedidoCompraResponse,
)
def enviar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
):
    try:
        return PedidoCompraService.enviar_pedido(
            db,
            pedido_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.post(
    "/{pedido_id}/cancelar",
    response_model=PedidoCompraResponse,
)
def cancelar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
):
    try:
        return PedidoCompraService.cancelar_pedido(
            db,
            pedido_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.post(
    "/{pedido_id}/recibir",
    response_model=PedidoCompraResponse,
)
def recibir_pedido(
    pedido_id: int,
    datos: RecepcionPedidoCreate,
    db: Session = Depends(get_db),
):
    try:
        return PedidoCompraService.recibir_mercancia(
            db,
            pedido_id,
            datos,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )
"""Alias de compatibilidad para rutas históricas de pedidos de compra."""
