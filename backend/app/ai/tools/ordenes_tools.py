from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models.orden_reparacion import OrdenReparacion
from app.models.vehiculo import Vehiculo


ORDENES_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_orden",
            "description": (
                "Busca órdenes, presupuestos o garantías de MotorDesk por "
                "número, avería, diagnóstico o estado."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {
                        "type": "string",
                        "description": (
                            "Número de orden, texto de avería, diagnóstico o "
                            "término de búsqueda."
                        ),
                    },
                },
                "required": ["texto"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_ordenes",
            "description": (
                "Lista órdenes de MotorDesk. Puede filtrar por estado y tipo. "
                "Úsala para órdenes abiertas, cerradas, facturadas, "
                "presupuestos o garantías."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "estado": {
                        "type": "string",
                        "description": "Estado exacto de las órdenes.",
                    },
                    "tipo": {
                        "type": "string",
                        "description": (
                            "Tipo de registro: OR, PR o GA."
                        ),
                    },
                    "limite": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "description": "Número máximo de resultados.",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_detalle_orden",
            "description": (
                "Obtiene el detalle de una orden concreta: vehículo, avería, "
                "diagnóstico, importes, mano de obra, piezas y facturas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "orden_id": {
                        "type": "integer",
                        "description": "ID interno de la orden.",
                    },
                },
                "required": ["orden_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_ordenes_cliente",
            "description": (
                "Obtiene el historial de órdenes de todos los vehículos de un "
                "cliente. Úsala después de identificar al cliente."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {
                        "type": "integer",
                        "description": "ID interno del cliente.",
                    },
                },
                "required": ["cliente_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_ordenes_vehiculo",
            "description": (
                "Obtiene el historial de reparaciones, presupuestos y garantías "
                "de un vehículo ya identificado."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vehiculo_id": {
                        "type": "integer",
                        "description": "ID interno del vehículo.",
                    },
                },
                "required": ["vehiculo_id"],
                "additionalProperties": False,
            },
        },
    },
]


def _serializar_orden(
    orden: OrdenReparacion,
) -> dict:
    vehiculo = None

    if orden.vehiculo:
        vehiculo = {
            "id": orden.vehiculo.id,
            "matricula": getattr(orden.vehiculo, "matricula", None),
            "marca": getattr(orden.vehiculo, "marca", None),
            "modelo": getattr(orden.vehiculo, "modelo", None),
        }

    return {
        "id": orden.id,
        "numero": orden.numero,
        "tipo": orden.tipo,
        "estado": orden.estado,
        "fecha_entrada": (
            orden.fecha_entrada.isoformat()
            if orden.fecha_entrada
            else None
        ),
        "fecha_salida": (
            orden.fecha_salida.isoformat()
            if orden.fecha_salida
            else None
        ),
        "descripcion_averia": orden.descripcion_averia,
        "diagnostico": orden.diagnostico,
        "importe_total": float(orden.importe_total or 0),
        "garantia": bool(orden.garantia),
        "vehiculo": vehiculo,
    }


def buscar_orden(
    db: Session,
    texto: str,
) -> list[dict]:
    texto = texto.strip()

    if not texto:
        return []

    patron = f"%{texto}%"
    ordenes = (
        db.query(OrdenReparacion)
        .options(selectinload(OrdenReparacion.vehiculo))
        .filter(
            or_(
                OrdenReparacion.numero.ilike(patron),
                OrdenReparacion.estado.ilike(patron),
                OrdenReparacion.descripcion_averia.ilike(patron),
                OrdenReparacion.diagnostico.ilike(patron),
            )
        )
        .order_by(OrdenReparacion.fecha_entrada.desc())
        .limit(20)
        .all()
    )

    return [_serializar_orden(orden) for orden in ordenes]


def listar_ordenes(
    db: Session,
    estado: str | None = None,
    tipo: str | None = None,
    limite: int = 20,
) -> list[dict]:
    limite = max(1, min(limite or 20, 50))
    query = db.query(OrdenReparacion).options(
        selectinload(OrdenReparacion.vehiculo)
    )

    if estado:
        query = query.filter(OrdenReparacion.estado == estado)

    if tipo:
        query = query.filter(OrdenReparacion.tipo == tipo)

    ordenes = (
        query.order_by(OrdenReparacion.fecha_entrada.desc())
        .limit(limite)
        .all()
    )

    return [_serializar_orden(orden) for orden in ordenes]


def obtener_detalle_orden(
    db: Session,
    orden_id: int,
) -> dict:
    if not orden_id:
        return {"encontrada": False}

    orden = (
        db.query(OrdenReparacion)
        .options(
            selectinload(OrdenReparacion.vehiculo),
            selectinload(OrdenReparacion.mano_obra),
            selectinload(OrdenReparacion.piezas),
            selectinload(OrdenReparacion.facturas),
            selectinload(OrdenReparacion.usuarios_asignados),
        )
        .filter(OrdenReparacion.id == orden_id)
        .first()
    )

    if not orden:
        return {"encontrada": False}

    resultado = _serializar_orden(orden)
    resultado.update(
        {
            "encontrada": True,
            "total_mano_obra": float(orden.total_mano_obra or 0),
            "total_piezas": float(orden.total_piezas or 0),
            "subtotal": float(orden.subtotal or 0),
            "base_imponible": float(orden.base_imponible or 0),
            "iva": float(orden.iva or 0),
            "importe_total": float(orden.importe_total or 0),
            "observaciones": orden.observaciones,
            "resolucion_garantia": orden.resolucion_garantia,
            "garantia_meses": orden.garantia_meses,
            "presupuesto_origen_id": orden.presupuesto_origen_id,
            "orden_origen_garantia_id": orden.orden_origen_garantia_id,
            "factura_origen_garantia_id": orden.factura_origen_garantia_id,
            "cita_origen_id": orden.cita_origen_id,
            "cantidad_mano_obra": len(orden.mano_obra or []),
            "cantidad_piezas": len(orden.piezas or []),
            "facturas": [
                {
                    "id": factura.id,
                    "numero": getattr(factura, "numero", None),
                    "estado": getattr(factura, "estado", None),
                    "total": float(getattr(factura, "total", 0) or 0),
                }
                for factura in (orden.facturas or [])
            ],
            "usuarios_asignados": [
                {
                    "id": usuario.id,
                    "nombre": getattr(usuario, "nombre", None),
                    "apellidos": getattr(usuario, "apellidos", None),
                }
                for usuario in (orden.usuarios_asignados or [])
            ],
        }
    )

    # No se incluyen observaciones_internas ni daños: no deben salir del
    # contexto operativo sin una herramienta y permiso específicos.
    return resultado


def obtener_ordenes_cliente(
    db: Session,
    cliente_id: int,
) -> list[dict]:
    if not cliente_id:
        return []

    ordenes = (
        db.query(OrdenReparacion)
        .join(Vehiculo, OrdenReparacion.vehiculo_id == Vehiculo.id)
        .options(selectinload(OrdenReparacion.vehiculo))
        .filter(Vehiculo.cliente_id == cliente_id)
        .order_by(OrdenReparacion.fecha_entrada.desc())
        .limit(50)
        .all()
    )

    return [_serializar_orden(orden) for orden in ordenes]


def obtener_ordenes_vehiculo(
    db: Session,
    vehiculo_id: int,
) -> list[dict]:
    if not vehiculo_id:
        return []

    ordenes = (
        db.query(OrdenReparacion)
        .options(selectinload(OrdenReparacion.vehiculo))
        .filter(OrdenReparacion.vehiculo_id == vehiculo_id)
        .order_by(OrdenReparacion.fecha_entrada.desc())
        .limit(50)
        .all()
    )

    return [_serializar_orden(orden) for orden in ordenes]
"""Herramientas IA de consulta de órdenes, presupuestos y estados de taller."""
