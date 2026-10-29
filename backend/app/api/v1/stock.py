"""Endpoints de almacén; los movimientos son la fuente de verdad del stock."""

from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.permissions import require_permission
from app.models.usuario import Usuario

from app.repositories.articulo_stock_repository import (
    ArticuloStockRepository
)

from app.repositories.movimiento_stock_repository import (
    MovimientoStockRepository
)

from app.schemas.articulo_stock import (
    ArticuloStockCreate,
    ArticuloStockUpdate,
    ArticuloStockResponse
)

from app.schemas.movimiento_stock import (
    MovimientoStockCreate,
    AjusteStockCreate,
    MovimientoStockResponse
)

from app.services.stock_service import (
    StockService
)


router = APIRouter(
    prefix="/stock",
    tags=["Stock / Almacén"]
)


@router.get(
    "/articulos",
    response_model=list[ArticuloStockResponse]
)
def listar_articulos(
    solo_activos: bool = False,
    controla_stock: bool | None = None,
    db: Session = Depends(get_db)
):
    return ArticuloStockRepository.get_all(
        db,
        solo_activos=solo_activos,
        controla_stock=controla_stock,
    )


@router.get(
    "/articulos/stock-bajo",
    response_model=list[ArticuloStockResponse]
)
def listar_stock_bajo(
    db: Session = Depends(get_db)
):
    return (
        ArticuloStockRepository
        .get_stock_bajo(db)
    )


@router.get(
    "/reposicion",
    response_model=list[ArticuloStockResponse]
)
def necesidades_reposicion(
    db: Session = Depends(get_db)
):
    return ArticuloStockRepository.get_stock_bajo(db)


@router.get(
    "/resumen"
)
def obtener_resumen_stock(
    db: Session = Depends(get_db)
):
    return StockService.obtener_resumen(db)


@router.get(
    "/mas-consumidos"
)
def articulos_mas_consumidos(
    limite: int = 10,
    db: Session = Depends(get_db)
):
    resultados = MovimientoStockRepository.get_mas_consumidos(
        db,
        limite
    )

    return [
        {
            "articulo_id": fila.articulo_id,
            "referencia": fila.referencia,
            "nombre": fila.nombre,
            "cantidad_consumida": fila.cantidad_consumida,
        }
        for fila in resultados
    ]


@router.get(
    "/articulos/{articulo_id}",
    response_model=ArticuloStockResponse
)
def obtener_articulo(
    articulo_id: int,
    db: Session = Depends(get_db)
):
    articulo = (
        ArticuloStockRepository.get_by_id(
            db,
            articulo_id
        )
    )

    if articulo is None:
        raise HTTPException(
            status_code=404,
            detail="Artículo no encontrado"
        )

    return articulo


@router.post(
    "/articulos",
    response_model=ArticuloStockResponse,
    status_code=status.HTTP_201_CREATED
)
def crear_articulo(
    datos: ArticuloStockCreate,
    db: Session = Depends(get_db)
):
    try:
        return StockService.crear_articulo(
            db,
            datos
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.patch(
    "/articulos/{articulo_id}",
    response_model=ArticuloStockResponse
)
def actualizar_articulo(
    articulo_id: int,
    datos: ArticuloStockUpdate,
    db: Session = Depends(get_db)
):
    try:
        return (
            StockService
            .actualizar_articulo(
                db,
                articulo_id,
                datos
            )
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.patch(
    "/articulos/{articulo_id}/estado",
    response_model=ArticuloStockResponse
)
def cambiar_estado_articulo(
    articulo_id: int,
    activo: bool,
    db: Session = Depends(get_db)
):
    try:
        return StockService.cambiar_estado_articulo(
            db,
            articulo_id,
            activo
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post(
    "/articulos/{articulo_id}/entrada",
    response_model=MovimientoStockResponse
)
def registrar_entrada(
    articulo_id: int,
    datos: MovimientoStockCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("stock.ajustar")
    ),
):
    try:
        return StockService.entrada(
            db,
            articulo_id,
            datos.cantidad,
            datos.motivo
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post(
    "/articulos/{articulo_id}/salida",
    response_model=MovimientoStockResponse
)
def registrar_salida(
    articulo_id: int,
    datos: MovimientoStockCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("stock.ajustar")
    ),
):
    try:
        return StockService.salida(
            db,
            articulo_id,
            datos.cantidad,
            datos.motivo
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post(
    "/articulos/{articulo_id}/ajuste-positivo",
    response_model=MovimientoStockResponse
)
def ajuste_positivo(
    articulo_id: int,
    datos: AjusteStockCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("stock.ajustar")
    ),
):
    try:
        return (
            StockService
            .ajuste_positivo(
                db,
                articulo_id,
                datos.cantidad,
                datos.motivo
            )
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post(
    "/articulos/{articulo_id}/ajuste-negativo",
    response_model=MovimientoStockResponse
)
def ajuste_negativo(
    articulo_id: int,
    datos: AjusteStockCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("stock.ajustar")
    ),
):
    try:
        return (
            StockService
            .ajuste_negativo(
                db,
                articulo_id,
                datos.cantidad,
                datos.motivo
            )
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get(
    "/articulos/{articulo_id}/movimientos",
    response_model=list[MovimientoStockResponse]
)
def movimientos_articulo(
    articulo_id: int,
    db: Session = Depends(get_db)
):
    articulo = (
        ArticuloStockRepository.get_by_id(
            db,
            articulo_id
        )
    )

    if articulo is None:
        raise HTTPException(
            status_code=404,
            detail="Artículo no encontrado"
        )

    return (
        MovimientoStockRepository
        .get_by_articulo(
            db,
            articulo_id
        )
    )


@router.get(
    "/movimientos",
    response_model=list[MovimientoStockResponse]
)
def listar_movimientos(
    db: Session = Depends(get_db)
):
    return (
        MovimientoStockRepository
        .get_all(db)
    )
