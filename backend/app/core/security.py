"""Primitivas de autenticación JWT usadas por los routers protegidos."""

from passlib.context import CryptContext

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.repositories.usuario_repository import UsuarioRepository

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )
    
def create_access_token(data: dict):
    """Firma un JWT de acceso; la caducidad procede de la configuración central."""

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)

def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Valida el JWT, recupera el usuario vigente y lo deja disponible para auditoría.

    No se confía en los datos del frontend: aunque Angular lea ``exp`` para
    redirigir de forma amigable, la firma, caducidad y existencia del usuario se
    comprueban aquí para cada endpoint protegido.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        email = payload.get("sub")

        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    usuario = UsuarioRepository.get_by_email(
        db,
        email
    )

    if usuario is None:
        raise credentials_exception

    # El middleware de auditoría HTTP utiliza este dato sin tener que volver a
    # decodificar el token ni realizar otra consulta a la base de datos.
    request.state.audit_user = {
        "id": usuario.id,
        "empresa_id": usuario.empresa_id,
    }
    return usuario
