from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.auth import RegisterRequest, Token
from app.services.auth_service import AuthService
from app.core.security import get_current_user
from app.schemas.usuario import UsuarioResponse

router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
)

_TIPOS_AVATAR_PERMITIDOS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
_TAMANO_MAXIMO_AVATAR = 5 * 1024 * 1024


@router.post("/me/avatar", response_model=UsuarioResponse)
async def subir_avatar(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if archivo.content_type not in _TIPOS_AVATAR_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selecciona una imagen JPG, PNG o WEBP",
        )

    contenido = await archivo.read()
    if not contenido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen seleccionada está vacía",
        )
    if len(contenido) > _TAMANO_MAXIMO_AVATAR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen no puede superar 5 MB",
        )

    directorio = Path("uploads") / "avatars"
    directorio.mkdir(parents=True, exist_ok=True)
    extension = _TIPOS_AVATAR_PERMITIDOS[archivo.content_type]
    nombre_archivo = f"usuario_{current_user.id}_{uuid4().hex}{extension}"
    ruta_nueva = directorio / nombre_archivo

    try:
        ruta_nueva.write_bytes(contenido)
        avatar_anterior = current_user.avatar_url
        current_user.avatar_url = f"/uploads/avatars/{nombre_archivo}"
        db.commit()
        db.refresh(current_user)

        if avatar_anterior and avatar_anterior.startswith("/uploads/avatars/"):
            ruta_anterior = Path(avatar_anterior.lstrip("/"))
            if ruta_anterior.exists():
                ruta_anterior.unlink()
    except Exception:
        db.rollback()
        if ruta_nueva.exists():
            ruta_nueva.unlink()
        raise

    return AuthService.obtener_usuario_actual(db, current_user)

@router.get("/me", response_model=UsuarioResponse)
def me(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return AuthService.obtener_usuario_actual(
        db,
        current_user,
    )

from app.schemas.auth import LoginRequest


@router.post("/register", response_model=Token, status_code=201)
def register(
    request: RegisterRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    try:
        return AuthService.registrar_usuario(
            db,
            request.nombre,
            request.apellidos,
            str(request.email),
            request.password,
            http_request.client.host if http_request.client else None,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/login", response_model=Token)
def login(
    request: LoginRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    try:

        return AuthService.login(
            db,
            request.email,
            request.password,
            http_request.client.host if http_request.client else None,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=401,
            detail=str(e)
        )
"""Endpoints públicos controlados de registro, acceso y perfil autenticado."""
