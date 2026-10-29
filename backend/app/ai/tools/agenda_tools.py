from datetime import datetime

from sqlalchemy.orm import Session, selectinload

from app.models.cita import Cita


AGENDA_TOOLS = [
    {"type": "function", "function": {"name": "listar_citas", "description": "Obtiene citas de Agenda dentro de un intervalo. Úsala para hoy, mañana, semana o una fecha concreta.", "parameters": {"type": "object", "properties": {"fecha_desde": {"type": "string", "description": "Inicio ISO 8601."}, "fecha_hasta": {"type": "string", "description": "Fin ISO 8601 exclusivo."}, "estado": {"type": "string", "description": "Pendiente, Confirmada, En taller, Completada, Cancelada o No presentado."}, "limite": {"type": "integer", "minimum": 1, "maximum": 100}}, "required": ["fecha_desde", "fecha_hasta"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_detalle_cita", "description": "Obtiene detalles, confirmación, recordatorio, reprogramación, orden y personal de una cita.", "parameters": {"type": "object", "properties": {"cita_id": {"type": "integer"}}, "required": ["cita_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_citas_cliente", "description": "Obtiene citas de un cliente identificado.", "parameters": {"type": "object", "properties": {"cliente_id": {"type": "integer"}, "solo_futuras": {"type": "boolean"}}, "required": ["cliente_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_citas_vehiculo", "description": "Obtiene citas de un vehículo identificado.", "parameters": {"type": "object", "properties": {"vehiculo_id": {"type": "integer"}, "solo_futuras": {"type": "boolean"}}, "required": ["vehiculo_id"], "additionalProperties": False}}},
]


def _cliente(cliente) -> dict | None:
    if cliente is None:
        return None
    return {"id": cliente.id, "nombre": cliente.nombre, "apellidos": cliente.apellidos, "telefono": cliente.telefono}


def _vehiculo(vehiculo) -> dict | None:
    if vehiculo is None:
        return None
    return {"id": vehiculo.id, "matricula": vehiculo.matricula, "marca": vehiculo.marca, "modelo": vehiculo.modelo}


def _serializar(cita: Cita) -> dict:
    return {
        "id": cita.id,
        "fecha_inicio": cita.fecha_inicio.isoformat() if cita.fecha_inicio else None,
        "fecha_fin": cita.fecha_fin.isoformat() if cita.fecha_fin else None,
        "motivo": cita.motivo,
        "estado": cita.estado,
        "cliente": _cliente(cita.cliente),
        "vehiculo": _vehiculo(cita.vehiculo),
        "orden_generada_id": cita.orden_generada_id,
    }


def _parsear_fecha(fecha: str) -> datetime:
    try:
        resultado = datetime.fromisoformat((fecha or "").replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise ValueError("La fecha recibida por MotorDesk AI no es válida.") from error

    # Las columnas de Agenda son DateTime sin zona. Convertimos una entrada con
    # zona horaria a hora local antes de compararla, evitando naive/aware errors.
    if resultado.tzinfo is not None:
        resultado = resultado.astimezone().replace(tzinfo=None)
    return resultado


def _query(db: Session):
    return db.query(Cita).options(selectinload(Cita.cliente), selectinload(Cita.vehiculo))


def listar_citas(db: Session, fecha_desde: str, fecha_hasta: str,
                 estado: str | None = None, limite: int = 50) -> list[dict]:
    desde, hasta = _parsear_fecha(fecha_desde), _parsear_fecha(fecha_hasta)
    if hasta <= desde:
        raise ValueError("El intervalo de fechas no es válido.")
    limite = max(1, min(int(limite or 50), 100))
    query = _query(db).filter(Cita.fecha_inicio >= desde, Cita.fecha_inicio < hasta)
    if estado:
        query = query.filter(Cita.estado == estado)
    return [_serializar(cita) for cita in query.order_by(Cita.fecha_inicio.asc(), Cita.id.asc()).limit(limite).all()]


def obtener_detalle_cita(db: Session, cita_id: int | None) -> dict:
    if not cita_id:
        return {"encontrada": False}
    cita = (_query(db).options(selectinload(Cita.orden_generada), selectinload(Cita.usuarios_asignados))
            .filter(Cita.id == cita_id).first())
    if cita is None:
        return {"encontrada": False}
    resultado = _serializar(cita)
    resultado.update({
        "encontrada": True, "observaciones": cita.observaciones,
        "fecha_confirmacion": cita.fecha_confirmacion.isoformat() if cita.fecha_confirmacion else None,
        "canal_confirmacion": cita.canal_confirmacion,
        "fecha_recordatorio": cita.fecha_recordatorio.isoformat() if cita.fecha_recordatorio else None,
        "canal_recordatorio": cita.canal_recordatorio,
        "fecha_reprogramacion": cita.fecha_reprogramacion.isoformat() if cita.fecha_reprogramacion else None,
        "fecha_inicio_anterior": cita.fecha_inicio_anterior.isoformat() if cita.fecha_inicio_anterior else None,
        "fecha_fin_anterior": cita.fecha_fin_anterior.isoformat() if cita.fecha_fin_anterior else None,
        "orden_generada": ({"id": cita.orden_generada.id, "numero": cita.orden_generada.numero, "estado": cita.orden_generada.estado} if cita.orden_generada else None),
        "usuarios_asignados": [{"id": usuario.id, "nombre": usuario.nombre, "apellidos": usuario.apellidos, "rol": usuario.rol} for usuario in cita.usuarios_asignados],
    })
    return resultado


def _por_campo(db: Session, campo, identificador: int | None, solo_futuras: bool = False) -> list[dict]:
    if not identificador:
        return []
    query = _query(db).filter(campo == identificador)
    if solo_futuras:
        query = query.filter(Cita.fecha_inicio >= datetime.now())
    return [_serializar(cita) for cita in query.order_by(Cita.fecha_inicio.desc(), Cita.id.desc()).limit(50).all()]


def obtener_citas_cliente(db: Session, cliente_id: int | None, solo_futuras: bool = False) -> list[dict]:
    return _por_campo(db, Cita.cliente_id, cliente_id, solo_futuras)


def obtener_citas_vehiculo(db: Session, vehiculo_id: int | None, solo_futuras: bool = False) -> list[dict]:
    return _por_campo(db, Cita.vehiculo_id, vehiculo_id, solo_futuras)
"""Herramientas IA de consulta de agenda, sin capacidad de reservar directamente."""
