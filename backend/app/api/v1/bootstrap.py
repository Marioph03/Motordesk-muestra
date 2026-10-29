"""Endpoints de solo lectura para el asistente de instalación inicial."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.bootstrap import BootstrapInicialRequest
from app.services.bootstrap_service import BootstrapService


router = APIRouter(
    prefix="/bootstrap",
    tags=["Bootstrap"],
)


@router.get("/status")
def obtener_estado_bootstrap(
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    """Devuelve si la instalación necesita completar la configuración inicial."""
    return {
        "requiere_configuracion": BootstrapService.necesita_configuracion(db),
    }


@router.post(
    "/inicializar",
    status_code=status.HTTP_201_CREATED,
)
def inicializar_motordesk(
    datos: BootstrapInicialRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Crea la primera empresa y el administrador una unica vez."""
    try:
        return BootstrapService.inicializar(db=db, datos=datos)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No se ha podido completar la configuracion porque alguno "
                "de los datos ya existe."
            ),
        ) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se ha podido completar la configuracion inicial de MotorDesk.",
        ) from exc
