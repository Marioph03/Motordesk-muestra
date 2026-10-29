from sqlalchemy.orm import Session, selectinload

from app.models.orden_reparacion import OrdenReparacion
from app.models.vehiculo import Vehiculo


GARANTIAS_TOOLS = [
    {"type": "function", "function": {"name": "listar_garantias", "description": "Lista garantías de MotorDesk y permite filtrar por estado.", "parameters": {"type": "object", "properties": {"estado": {"type": "string", "description": "Garantía abierta, En revisión, Garantía aprobada, Garantía rechazada, En reparación o Resuelta."}, "limite": {"type": "integer", "minimum": 1, "maximum": 100}}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_detalle_garantia", "description": "Obtiene vehículo, motivo, resolución y orden o factura de origen de una garantía.", "parameters": {"type": "object", "properties": {"garantia_id": {"type": "integer"}}, "required": ["garantia_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_garantias_vehiculo", "description": "Obtiene garantías de un vehículo.", "parameters": {"type": "object", "properties": {"vehiculo_id": {"type": "integer"}}, "required": ["vehiculo_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_garantias_cliente", "description": "Obtiene garantías de todos los vehículos de un cliente.", "parameters": {"type": "object", "properties": {"cliente_id": {"type": "integer"}}, "required": ["cliente_id"], "additionalProperties": False}}},
]


def _numero(valor) -> float:
    return float(valor or 0)


def _serializar(garantia: OrdenReparacion) -> dict:
    vehiculo = garantia.vehiculo
    return {
        "id": garantia.id, "numero": garantia.numero, "tipo": garantia.tipo, "estado": garantia.estado,
        "fecha_entrada": garantia.fecha_entrada.isoformat() if garantia.fecha_entrada else None,
        "fecha_salida": garantia.fecha_salida.isoformat() if garantia.fecha_salida else None,
        "motivo": garantia.descripcion_averia, "diagnostico": garantia.diagnostico,
        "resolucion": garantia.resolucion_garantia, "garantia_meses": garantia.garantia_meses,
        "importe_total": _numero(garantia.importe_total),
        "vehiculo": ({"id": vehiculo.id, "matricula": vehiculo.matricula, "marca": vehiculo.marca, "modelo": vehiculo.modelo} if vehiculo else None),
        "orden_origen_id": garantia.orden_origen_garantia_id,
        "factura_origen_id": garantia.factura_origen_garantia_id,
    }


def _query(db: Session):
    # El tipo interno real de garantía en MotorDesk es GA.
    return db.query(OrdenReparacion).options(selectinload(OrdenReparacion.vehiculo)).filter(OrdenReparacion.tipo == "GA")


def _limite(valor: int, defecto: int = 50) -> int:
    return max(1, min(int(valor or defecto), 100))


def listar_garantias(db: Session, estado: str | None = None, limite: int = 50) -> list[dict]:
    query = _query(db)
    if estado:
        query = query.filter(OrdenReparacion.estado == estado)
    return [_serializar(garantia) for garantia in query.order_by(OrdenReparacion.fecha_entrada.desc(), OrdenReparacion.id.desc()).limit(_limite(limite)).all()]


def obtener_detalle_garantia(db: Session, garantia_id: int | None) -> dict:
    if not garantia_id:
        return {"encontrada": False}
    garantia = (_query(db).options(selectinload(OrdenReparacion.orden_origen_garantia),
        selectinload(OrdenReparacion.factura_origen_garantia), selectinload(OrdenReparacion.mano_obra),
        selectinload(OrdenReparacion.piezas)).filter(OrdenReparacion.id == garantia_id).first())
    if garantia is None:
        return {"encontrada": False}
    resultado = _serializar(garantia)
    resultado.update({"encontrada": True, "observaciones": garantia.observaciones,
        "total_mano_obra": _numero(garantia.total_mano_obra), "total_piezas": _numero(garantia.total_piezas),
        "fecha_resolucion": garantia.fecha_resolucion_garantia.isoformat() if garantia.fecha_resolucion_garantia else None,
        "orden_origen": ({"id": garantia.orden_origen_garantia.id, "numero": garantia.orden_origen_garantia.numero, "estado": garantia.orden_origen_garantia.estado} if garantia.orden_origen_garantia else None),
        "factura_origen": ({"id": garantia.factura_origen_garantia.id, "numero": garantia.factura_origen_garantia.numero, "estado": garantia.factura_origen_garantia.estado, "total": _numero(garantia.factura_origen_garantia.total)} if garantia.factura_origen_garantia else None),
        "cantidad_operaciones_mano_obra": len(garantia.mano_obra), "cantidad_piezas": len(garantia.piezas)})
    return resultado


def obtener_garantias_vehiculo(db: Session, vehiculo_id: int | None) -> list[dict]:
    if not vehiculo_id:
        return []
    return [_serializar(garantia) for garantia in _query(db).filter(OrdenReparacion.vehiculo_id == vehiculo_id).order_by(OrdenReparacion.fecha_entrada.desc(), OrdenReparacion.id.desc()).limit(50).all()]


def obtener_garantias_cliente(db: Session, cliente_id: int | None) -> list[dict]:
    if not cliente_id:
        return []
    garantias = (_query(db).join(Vehiculo, OrdenReparacion.vehiculo_id == Vehiculo.id).filter(Vehiculo.cliente_id == cliente_id)
                 .order_by(OrdenReparacion.fecha_entrada.desc(), OrdenReparacion.id.desc()).limit(50).all())
    return [_serializar(garantia) for garantia in garantias]
"""Herramientas IA de garantías, modeladas como órdenes tipo GA."""
