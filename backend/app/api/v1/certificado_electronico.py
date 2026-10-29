from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.database import get_db
from app.models.usuario import Usuario
from app.schemas.certificado_electronico import (
    CertificadoElectronicoEstadoResponse,
    CertificadoElectronicoResponse,
)
from app.services.certificado_electronico_service import (
    CertificadoElectronicoService,
)


router = APIRouter(
    prefix="/configuracion/certificado-electronico",
    tags=[
        "Configuración - Certificado electrónico"
    ],
)


async def _leer_certificado(archivo: UploadFile) -> bytes:
    """Lee el adjunto con límite real de memoria, también sin Content-Length."""
    partes: list[bytes] = []
    total = 0
    while bloque := await archivo.read(1024 * 1024):
        total += len(bloque)
        if total > CertificadoElectronicoService.TAMANO_MAXIMO:
            raise ValueError(
                "El certificado supera el tamaño máximo permitido de 10 MB."
            )
        partes.append(bloque)
    return b"".join(partes)


def _empresa_id_usuario(
    current_user: Usuario,
) -> int:

    if current_user.empresa_id is None:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "El usuario autenticado "
                "no tiene una empresa asignada."
            ),
        )

    return current_user.empresa_id


@router.get(
    "",
    response_model=CertificadoElectronicoResponse,
)
def obtener_certificado(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_permission(
            "permisos.gestionar"
        )
    ),
):

    certificado = (
        CertificadoElectronicoService
        .obtener(
            db,
            _empresa_id_usuario(
                current_user
            ),
        )
    )

    if (
        certificado is None
        or not CertificadoElectronicoService.archivo_disponible(certificado)
    ):

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No hay ningún certificado "
                "electrónico configurado."
            ),
        )

    return certificado


@router.get(
    "/estado",
    response_model=(
        CertificadoElectronicoEstadoResponse
    ),
)
def obtener_estado_certificado(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_permission(
            "permisos.gestionar"
        )
    ),
):

    certificado = (
        CertificadoElectronicoService
        .obtener(
            db,
            _empresa_id_usuario(
                current_user
            ),
        )
    )

    if (
        certificado is None
        or not CertificadoElectronicoService.archivo_disponible(certificado)
    ):

        return (
            CertificadoElectronicoEstadoResponse(
                configurado=False,
                activo=False,
                caducado=False,
            )
        )

    return (
        CertificadoElectronicoEstadoResponse(
            configurado=True,
            activo=certificado.activo,

            nombre_archivo=(
                certificado.nombre_archivo
            ),

            titular=(
                certificado.titular
            ),

            nif_titular=(
                certificado.nif_titular
            ),

            emisor=(
                certificado.emisor
            ),

            fecha_validez_desde=(
                certificado
                .fecha_validez_desde
            ),

            fecha_caducidad=(
                certificado
                .fecha_caducidad
            ),

            caducado=(
                CertificadoElectronicoService
                .esta_caducado(
                    certificado
                )
            ),
        )
    )


@router.post(
    "",
    response_model=CertificadoElectronicoResponse,
)
async def guardar_certificado(
    archivo: UploadFile = File(...),
    password: str = Form(...),

    db: Session = Depends(get_db),

    current_user: Usuario = Depends(
        require_permission(
            "permisos.gestionar"
        )
    ),
):

    try:

        if not archivo.filename:

            raise ValueError(
                "El archivo no tiene nombre."
            )

        contenido = await _leer_certificado(archivo)

        return (
            CertificadoElectronicoService
            .guardar(
                db=db,

                empresa_id=(
                    _empresa_id_usuario(
                        current_user
                    )
                ),

                nombre_archivo=(
                    archivo.filename
                ),

                contenido=contenido,

                password=password,
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=str(exc),
        ) from exc

    finally:

        await archivo.close()


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar_certificado(
    db: Session = Depends(get_db),

    current_user: Usuario = Depends(
        require_permission(
            "permisos.gestionar"
        )
    ),
):

    try:

        CertificadoElectronicoService.eliminar(
            db,
            _empresa_id_usuario(
                current_user
            ),
        )

        return Response(
            status_code=(
                status.HTTP_204_NO_CONTENT
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(exc),
        ) from exc
