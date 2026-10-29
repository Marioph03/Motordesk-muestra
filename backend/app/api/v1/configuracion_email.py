from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.database import get_db
from app.models.usuario import Usuario
from app.schemas.configuracion_email import ConfiguracionEmailGuardar, ConfiguracionEmailResponse, PruebaEmailRequest
from app.services.configuracion_email_service import ConfiguracionEmailService
from app.services.google_email_oauth_service import GoogleEmailOAuthService
from app.services.microsoft_email_oauth_service import MicrosoftEmailOAuthService

router = APIRouter(prefix="/configuracion/email", tags=["Configuración - Correo"])

def empresa_id(usuario: Usuario) -> int:
    if usuario.empresa_id is None: raise HTTPException(403, "El usuario no tiene una empresa asignada.")
    return usuario.empresa_id

@router.get("", response_model=ConfiguracionEmailResponse)
def obtener(db: Session = Depends(get_db), usuario: Usuario = Depends(require_permission("permisos.gestionar"))):
    return ConfiguracionEmailService.respuesta(ConfiguracionEmailService.obtener(db, empresa_id(usuario)))

@router.put("", response_model=ConfiguracionEmailResponse)
def guardar(datos: ConfiguracionEmailGuardar, db: Session = Depends(get_db), usuario: Usuario = Depends(require_permission("permisos.gestionar"))):
    try:
        return ConfiguracionEmailService.respuesta(ConfiguracionEmailService.guardar(db, empresa_id(usuario), datos))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

@router.post("/probar")
def probar(datos: PruebaEmailRequest, db: Session = Depends(get_db), usuario: Usuario = Depends(require_permission("permisos.gestionar"))):
    try:
        ConfiguracionEmailService.enviar_prueba(db, empresa_id(usuario), str(datos.destinatario))
        return {"message": "Correo de prueba enviado correctamente."}
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(400, str(exc)) from exc

@router.post("/google/iniciar")
def google_iniciar(usuario: Usuario = Depends(require_permission("permisos.gestionar"))):
    return GoogleEmailOAuthService.iniciar(empresa_id(usuario))

@router.get("/google/callback")
def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    try:
        GoogleEmailOAuthService.completar(db, code, state)
        return "<html><body><p>Correo conectado. Puedes cerrar esta ventana.</p><script>window.close()</script></body></html>"
    except (ValueError, RuntimeError) as exc:
        return f"<html><body><p>No se pudo conectar el correo: {str(exc)}</p></body></html>"

@router.get("/google/estado/{state}")
def google_estado(state: str, usuario: Usuario = Depends(require_permission("permisos.gestionar"))):
    empresa = empresa_id(usuario)
    return {
        "estado": GoogleEmailOAuthService.estado(state, empresa),
        "detalle": GoogleEmailOAuthService.detalle_estado(state, empresa),
    }

@router.post("/microsoft/iniciar")
def microsoft_iniciar(usuario: Usuario = Depends(require_permission("permisos.gestionar"))):
    return MicrosoftEmailOAuthService.iniciar(empresa_id(usuario))

@router.get("/microsoft/callback")
def microsoft_callback(code: str, state: str, db: Session = Depends(get_db)):
    try:
        MicrosoftEmailOAuthService.completar(db, code, state)
        return "<html><body><p>Correo conectado. Puedes cerrar esta ventana.</p><script>window.close()</script></body></html>"
    except (ValueError, RuntimeError) as exc:
        return f"<html><body><p>No se pudo conectar el correo: {str(exc)}</p></body></html>"

@router.get("/microsoft/estado/{state}")
def microsoft_estado(state: str, usuario: Usuario = Depends(require_permission("permisos.gestionar"))):
    return {"estado": MicrosoftEmailOAuthService.estado(state, empresa_id(usuario))}
