from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.ai.actions.action_models import AccionPendiente, EstadoAccion, TipoAccion
from app.ai.actions.action_store import action_store
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.schemas.cita import CitaCreate
from app.services.cita_service import CitaService
from app.services.permisos_service import PermisosService


def _parsear_fecha(valor: str | None) -> datetime:
    try:
        fecha = datetime.fromisoformat((valor or "").replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise ValueError("La fecha de la cita no es válida.") from error
    if fecha.tzinfo is not None:
        fecha = fecha.astimezone().replace(tzinfo=None)
    return fecha


def verificar_permiso_crear_cita(
    db: Session,
    usuario_id: int
) -> None:
    usuario = (
        db.query(Usuario)
        .filter(Usuario.id == usuario_id)
        .first()
    )

    if usuario is None or not usuario.activo:
        raise PermissionError(
            "El usuario no puede crear citas."
        )

    if not PermisosService.usuario_tiene_permiso(
        db,
        usuario,
        "agenda.crear"
    ):
        raise PermissionError(
            "No tienes permiso para crear citas."
        )


def _obtener_y_validar_datos(db: Session, datos: dict) -> dict:
    cliente_id, vehiculo_id = datos.get("cliente_id"), datos.get("vehiculo_id")
    motivo = str(datos.get("motivo") or "").strip()
    if not cliente_id:
        raise ValueError("La cita necesita un cliente.")
    if not vehiculo_id:
        raise ValueError("La cita necesita un vehículo.")
    if not motivo:
        raise ValueError("La cita necesita un motivo.")
    if len(motivo) > 500:
        raise ValueError("El motivo de la cita es demasiado largo.")

    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if cliente is None:
        raise ValueError("El cliente ya no existe.")
    if vehiculo is None:
        raise ValueError("El vehículo ya no existe.")
    if vehiculo.cliente_id != cliente.id:
        raise ValueError("El vehículo seleccionado no pertenece al cliente.")

    fecha_inicio = _parsear_fecha(datos.get("fecha_inicio"))
    fecha_fin = _parsear_fecha(datos.get("fecha_fin")) if datos.get("fecha_fin") else fecha_inicio + timedelta(hours=1)
    if fecha_inicio < datetime.now():
        raise ValueError("No se puede crear una cita en el pasado.")
    # Reutiliza duración y horario configurado. CitaService.create() repetirá
    # todas las validaciones durante la confirmación para evitar carreras.
    CitaService._validar_fechas(fecha_inicio, fecha_fin)
    from app.services.configuracion_agenda_service import ConfiguracionAgendaService
    ConfiguracionAgendaService.validar_fecha_cita(db, fecha_inicio, fecha_fin)

    return {"cliente": cliente, "vehiculo": vehiculo, "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin, "motivo": motivo,
            "observaciones": str(datos.get("observaciones") or "").strip() or None}


def ejecutar_crear_cita(db: Session, accion: AccionPendiente, usuario_id: int) -> dict:
    if accion.tipo != TipoAccion.CREAR_CITA:
        raise ValueError("La acción no corresponde a una cita.")
    if accion.usuario_id != usuario_id:
        raise PermissionError("La acción pertenece a otro usuario.")
    if accion.estado != EstadoAccion.PENDIENTE:
        raise ValueError("La acción ya no está pendiente.")

    verificar_permiso_crear_cita(db, usuario_id)
    validado = _obtener_y_validar_datos(db, accion.datos)
    # Esta llamada es la fuente única de validación/commit de Agenda.
    cita = CitaService.create(db, CitaCreate(
        cliente_id=validado["cliente"].id,
        vehiculo_id=validado["vehiculo"].id,
        usuarios_ids=[],
        fecha_inicio=validado["fecha_inicio"],
        fecha_fin=validado["fecha_fin"],
        motivo=validado["motivo"],
        observaciones=validado["observaciones"],
    ))

    ahora = datetime.utcnow().isoformat()
    accion.estado = EstadoAccion.EJECUTADA
    accion.confirmada_en = ahora
    accion.ejecutada_en = ahora
    accion.resultado = {"cita_id": cita.id, "cliente_id": cita.cliente_id,
                       "vehiculo_id": cita.vehiculo_id, "fecha_inicio": cita.fecha_inicio.isoformat(),
                       "fecha_fin": cita.fecha_fin.isoformat(), "estado": cita.estado}
    action_store.guardar(accion)
    return {"ok": True, "mensaje": "Cita creada correctamente.", "cita": accion.resultado}
"""Propuesta y ejecución confirmada de una cita desde MotorDesk AI."""
