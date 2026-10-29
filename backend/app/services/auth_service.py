from sqlalchemy.orm import Session

from app.core.security import (
    verify_password,
    create_access_token,
    get_password_hash,
)
from app.repositories.usuario_repository import UsuarioRepository
from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.rol_repository import RolRepository
from app.models.usuario import Usuario
from app.services.actividad_service import ActividadService
from app.services.permisos_service import PermisosService
from app.schemas.usuario import UsuarioResponse


class AuthService:

    @staticmethod
    def registrar_usuario(
        db: Session,
        nombre: str,
        apellidos: str,
        email: str,
        password: str,
        ip: str | None = None,
    ):
        """Registra una cuenta de acceso con privilegios iniciales limitados."""
        if UsuarioRepository.get_by_email(db, email) is not None:
            raise ValueError("Ya existe una cuenta con este correo")

        rol = RolRepository.get_by_nombre(db, "RECEPCION")
        if rol is None or not rol.activo:
            raise ValueError(
                "No está disponible el rol inicial para registrar usuarios"
            )

        empresa = EmpresaRepository.get_first(db)
        if empresa is None:
            raise ValueError(
                "Configura primero los datos de la empresa"
            )

        usuario = Usuario(
            nombre=nombre.strip(),
            apellidos=apellidos.strip(),
            email=email.lower().strip(),
            password_hash=get_password_hash(password),
            rol=rol.nombre,
            activo=True,
            empresa_id=empresa.id,
        )

        try:
            db.add(usuario)
            db.commit()
            db.refresh(usuario)
        except Exception:
            db.rollback()
            raise

        ActividadService.registrar_evento(
            db,
            empresa_id=usuario.empresa_id,
            usuario_id=usuario.id,
            modulo="AUTENTICACION",
            accion="REGISTRO_USUARIO",
            descripcion="Cuenta registrada desde la pantalla de acceso",
            ip=ip,
        )

        return AuthService.login(db, email, password, ip)

    @staticmethod
    def obtener_usuario_actual(
        db: Session,
        usuario,
    ) -> dict:
        """Construye la información de sesión que consume Angular."""

        datos = UsuarioResponse.model_validate(
            usuario
        ).model_dump()

        datos["permisos"] = (
            PermisosService.obtener_codigos_usuario(
                db,
                usuario,
            )
        )

        return datos

    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str
    ):

        email_normalizado = (email or "").strip().lower()

        usuario = UsuarioRepository.get_by_email(
            db,
            email_normalizado
        )

        if usuario is None:
            return None

        if not verify_password(
            password,
            usuario.password_hash
        ):
            return None

        return usuario

    @staticmethod
    def login(
        db: Session,
        email: str,
        password: str,
        ip: str | None = None,
    ):

        email_normalizado = (email or "").strip().lower()

        usuario = AuthService.authenticate_user(
            db,
            email_normalizado,
            password
        )

        if usuario is None:
            raise ValueError(
                "Email o contraseña incorrectos"
            )

        access_token = create_access_token(
            {
                "sub": usuario.email
            }
        )

        ActividadService.registrar_evento(
            db,
            empresa_id=usuario.empresa_id,
            usuario_id=usuario.id,
            modulo="AUTENTICACION",
            accion="INICIO_SESION",
            descripcion="Inicio de sesión correcto",
            ip=ip,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "usuario": AuthService.obtener_usuario_actual(
                db,
                usuario,
            ),
        }
