from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models.factura import Factura


FACTURAS_TOOLS = [
    {"type": "function", "function": {"name": "buscar_factura", "description": "Busca facturas por número, estado, cobro, tipo o documento.", "parameters": {"type": "object", "properties": {"texto": {"type": "string", "description": "Texto de búsqueda."}}, "required": ["texto"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "listar_facturas", "description": "Lista facturas con filtros opcionales.", "parameters": {"type": "object", "properties": {"estado": {"type": "string", "description": "BORRADOR, EMITIDA o ANULADA."}, "estado_cobro": {"type": "string", "description": "PENDIENTE, PARCIAL o PAGADA."}, "tipo_factura": {"type": "string", "description": "REPARACION, PRESUPUESTO o GARANTIA."}, "es_prueba": {"type": "boolean", "description": "Filtra facturas de prueba o reales."}, "limite": {"type": "integer", "minimum": 1, "maximum": 50}}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_detalle_factura", "description": "Obtiene detalle de factura, líneas, pagos, cliente, vehículo, orden y VERIFACTU.", "parameters": {"type": "object", "properties": {"factura_id": {"type": "integer"}}, "required": ["factura_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_facturas_cliente", "description": "Obtiene el historial de facturas de un cliente.", "parameters": {"type": "object", "properties": {"cliente_id": {"type": "integer"}}, "required": ["cliente_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_facturas_vehiculo", "description": "Obtiene el historial de facturas de un vehículo.", "parameters": {"type": "object", "properties": {"vehiculo_id": {"type": "integer"}}, "required": ["vehiculo_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_facturas_orden", "description": "Obtiene facturas vinculadas a una orden de reparación.", "parameters": {"type": "object", "properties": {"orden_id": {"type": "integer"}}, "required": ["orden_id"], "additionalProperties": False}}},
]


def _numero(valor) -> float:
    return float(valor or 0)


def _cliente(cliente) -> dict | None:
    if cliente is None:
        return None
    return {"id": cliente.id, "nombre": cliente.nombre, "apellidos": cliente.apellidos,
            "telefono": cliente.telefono, "email": cliente.email}


def _vehiculo(vehiculo) -> dict | None:
    if vehiculo is None:
        return None
    return {"id": vehiculo.id, "matricula": vehiculo.matricula,
            "marca": vehiculo.marca, "modelo": vehiculo.modelo}


def _serializar(factura: Factura) -> dict:
    return {
        "id": factura.id, "numero": factura.numero,
        "tipo_documento": factura.tipo_documento, "tipo_factura": factura.tipo_factura,
        "estado": factura.estado, "estado_cobro": factura.estado_cobro,
        "fecha_emision": factura.fecha_emision.isoformat() if factura.fecha_emision else None,
        "total": _numero(factura.total), "es_prueba": bool(factura.es_prueba),
        "modo_facturacion": factura.modo_facturacion,
        "enviada_verifactu": bool(factura.enviada_verifactu),
        "cliente": _cliente(factura.cliente), "vehiculo": _vehiculo(factura.vehiculo),
        "orden_id": factura.orden_id,
    }


def _query(db: Session):
    return db.query(Factura).options(selectinload(Factura.cliente), selectinload(Factura.vehiculo))


def buscar_factura(db: Session, texto: str) -> list[dict]:
    texto = (texto or "").strip()
    if not texto:
        return []
    patron = f"%{texto}%"
    facturas = (_query(db).filter(or_(Factura.numero.ilike(patron), Factura.estado.ilike(patron),
        Factura.estado_cobro.ilike(patron), Factura.tipo_factura.ilike(patron),
        Factura.tipo_documento.ilike(patron))).order_by(Factura.fecha_emision.desc(), Factura.id.desc()).limit(20).all())
    return [_serializar(factura) for factura in facturas]


def listar_facturas(db: Session, estado: str | None = None, estado_cobro: str | None = None,
                    tipo_factura: str | None = None, es_prueba: bool | None = None,
                    limite: int = 20) -> list[dict]:
    query = _query(db)
    if estado:
        query = query.filter(Factura.estado == estado.upper())
    if estado_cobro:
        query = query.filter(Factura.estado_cobro == estado_cobro.upper())
    if tipo_factura:
        query = query.filter(Factura.tipo_factura == tipo_factura.upper())
    if es_prueba is not None:
        query = query.filter(Factura.es_prueba == es_prueba)
    limite = max(1, min(int(limite or 20), 50))
    return [_serializar(factura) for factura in query.order_by(Factura.fecha_emision.desc(), Factura.id.desc()).limit(limite).all()]


def obtener_detalle_factura(db: Session, factura_id: int | None) -> dict:
    if not factura_id:
        return {"encontrada": False}
    factura = (_query(db).options(selectinload(Factura.orden), selectinload(Factura.lineas), selectinload(Factura.pagos))
               .filter(Factura.id == factura_id).first())
    if factura is None:
        return {"encontrada": False}
    resultado = _serializar(factura)
    resultado.update({
        "encontrada": True, "subtotal": _numero(factura.subtotal),
        "descuento_porcentaje": _numero(factura.descuento_porcentaje),
        "base_imponible": _numero(factura.base_imponible), "iva": _numero(factura.iva),
        "cuota_iva": _numero(factura.cuota_iva), "observaciones": factura.observaciones,
        "fecha_envio_verifactu": factura.fecha_envio_verifactu.isoformat() if factura.fecha_envio_verifactu else None,
        "orden": ({"id": factura.orden.id, "numero": factura.orden.numero, "estado": factura.orden.estado} if factura.orden else None),
        "lineas": [{"id": linea.id, "origen": linea.origen, "descripcion": linea.descripcion,
                    "cantidad": _numero(linea.cantidad), "precio_unitario": _numero(linea.precio_unitario),
                    "descuento_porcentaje": _numero(linea.descuento_porcentaje), "subtotal": _numero(linea.subtotal),
                    "iva": _numero(linea.iva), "total": _numero(linea.total)} for linea in factura.lineas],
        "pagos_registrados": len(factura.pagos),
    })
    return resultado


def _por_campo(db: Session, campo, identificador: int | None, limite: int | None = 50) -> list[dict]:
    if not identificador:
        return []
    query = _query(db).filter(campo == identificador).order_by(Factura.fecha_emision.desc(), Factura.id.desc())
    if limite is not None:
        query = query.limit(limite)
    return [_serializar(factura) for factura in query.all()]


def obtener_facturas_cliente(db: Session, cliente_id: int | None) -> list[dict]:
    return _por_campo(db, Factura.cliente_id, cliente_id)


def obtener_facturas_vehiculo(db: Session, vehiculo_id: int | None) -> list[dict]:
    return _por_campo(db, Factura.vehiculo_id, vehiculo_id)


def obtener_facturas_orden(db: Session, orden_id: int | None) -> list[dict]:
    return _por_campo(db, Factura.orden_id, orden_id, limite=None)
"""Herramientas IA de consulta de facturas, nunca de escritura fiscal directa."""
