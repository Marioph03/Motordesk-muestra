from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.permissions import require_permission
from app.database.database import get_db
from app.models.devolucion_proveedor import DevolucionProveedor
from app.models.usuario import Usuario
from app.schemas.devolucion_proveedor import (
    DevolucionProveedorCreate,
    DevolucionProveedorResponse,
    ResolverDevolucionRequest,
)
from app.services.devolucion_proveedor_service import DevolucionProveedorService


router = APIRouter(
    prefix="/devoluciones-proveedor",
    tags=["Devoluciones a proveedor"],
)


@router.get("", response_model=list[DevolucionProveedorResponse])
def listar_devoluciones(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("compras.ver")),
):
    """Lista las devoluciones con sus líneas ya cargadas.

    Precargar las relaciones evita que la serialización de la respuesta dependa
    de cargas diferidas de SQLAlchemy, que en instalaciones con datos antiguos
    podía hacer que el listado fallase o apareciese vacío.
    """
    return (
        db.query(DevolucionProveedor)
        .options(selectinload(DevolucionProveedor.lineas))
        .order_by(DevolucionProveedor.fecha.desc(), DevolucionProveedor.id.desc())
        .all()
    )


@router.get("/{devolucion_id}", response_model=DevolucionProveedorResponse)
def obtener_devolucion(
    devolucion_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("compras.ver")),
):
    try:
        return DevolucionProveedorService._obtener(db, devolucion_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post(
    "",
    response_model=DevolucionProveedorResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_devolucion(
    datos: DevolucionProveedorCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("compras.crear")),
):
    try:
        return DevolucionProveedorService.crear(db, datos)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{devolucion_id}/confirmar", response_model=DevolucionProveedorResponse)
def confirmar_devolucion(
    devolucion_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("compras.recibir")),
):
    try:
        return DevolucionProveedorService.confirmar(db, devolucion_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{devolucion_id}/resolver", response_model=DevolucionProveedorResponse)
def resolver_devolucion(
    devolucion_id: int,
    datos: ResolverDevolucionRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("compras.recibir")),
):
    try:
        return DevolucionProveedorService.resolver(
            db,
            devolucion_id,
            datos.resolucion,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
"""API para crear y confirmar devoluciones de mercancía a proveedores."""
