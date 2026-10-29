from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario

from app.services.verifactu_service import (
    VerifactuService
)

from app.services.verifactu_aeat_service import (
    VerifactuAeatService
)
from app.schemas.registro_verifactu import RegistroVerifactuResponse


router = APIRouter(
    prefix="/verifactu",
    tags=["VERI*FACTU"],
    dependencies=[Depends(get_current_user)]
)


def _empresa_id_usuario(current_user: Usuario) -> int:
    if current_user.empresa_id is None:
        raise HTTPException(
            status_code=403,
            detail="El usuario autenticado no tiene una empresa asignada.",
        )
    return current_user.empresa_id


@router.get(
    "/facturas/{factura_id}/registros",
    response_model=list[RegistroVerifactuResponse],
)
def get_registros_factura(
    factura_id: int,
    db: Session = Depends(get_db),
):
    try:
        return VerifactuService.get_registros_factura(db, factura_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/facturas/{factura_id}/generar"
)
def generar_registro(
    factura_id: int,
    db: Session = Depends(get_db)
):

    try:

        registro = (
            VerifactuService.generar_registro_alta(
                db,
                factura_id
            )
        )

        return {
            "id": registro.id,
            "factura_id": registro.factura_id,
            "tipo_registro": registro.tipo_registro,
            "estado": registro.estado,
            "hash_registro":
                registro.hash_registro
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post(
    "/facturas/{factura_id}/generar-anulacion"
)
def generar_registro_anulacion(
    factura_id: int,
    db: Session = Depends(get_db),
):
    try:
        registro = VerifactuService.generar_registro_anulacion(db, factura_id)
        return {
            "id": registro.id,
            "factura_id": registro.factura_id,
            "tipo_registro": registro.tipo_registro,
            "estado": registro.estado,
            "hash_registro": registro.hash_registro,
            "hash_anterior": registro.hash_anterior,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/registros/{registro_id}/enviar-test"
)
def enviar_registro_test(
    registro_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):

    try:

        return (
            VerifactuAeatService
            .enviar_registro_test(
                db,
                registro_id,
                _empresa_id_usuario(current_user),
            )
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post("/registros/{registro_id}/enviar")
def enviar_registro_produccion(
    registro_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return VerifactuAeatService.enviar_registro_produccion(
            db,
            registro_id,
            _empresa_id_usuario(current_user),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
"""Consulta y reintento controlado de los registros fiscales VERI*FACTU."""
