from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models.albaran_proveedor import AlbaranProveedor
from app.models.devolucion_proveedor import DevolucionProveedor
from app.models.linea_albaran_proveedor import LineaAlbaranProveedor
from app.models.linea_devolucion_proveedor import LineaDevolucionProveedor
from app.models.pedido_compra import PedidoCompra


COMPRAS_TOOLS = [
    {"type": "function", "function": {"name": "buscar_pedido_compra", "description": "Busca pedidos de compra por número o estado.", "parameters": {"type": "object", "properties": {"texto": {"type": "string"}}, "required": ["texto"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "listar_pedidos_compra", "description": "Lista pedidos de compra por proveedor o estado: BORRADOR, ENVIADO, RECIBIDO_PARCIAL, RECIBIDO y CANCELADO.", "parameters": {"type": "object", "properties": {"proveedor_id": {"type": "integer"}, "estado": {"type": "string"}, "limite": {"type": "integer", "minimum": 1, "maximum": 100}}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_detalle_pedido_compra", "description": "Obtiene proveedor, importes y líneas con cantidades pedidas y recibidas.", "parameters": {"type": "object", "properties": {"pedido_id": {"type": "integer"}}, "required": ["pedido_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "buscar_albaran_proveedor", "description": "Busca albaranes por número interno o número de proveedor.", "parameters": {"type": "object", "properties": {"texto": {"type": "string"}}, "required": ["texto"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "listar_albaranes_proveedor", "description": "Lista albaranes de proveedor, opcionalmente por proveedor.", "parameters": {"type": "object", "properties": {"proveedor_id": {"type": "integer"}, "limite": {"type": "integer", "minimum": 1, "maximum": 100}}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_detalle_albaran_proveedor", "description": "Obtiene artículos, cantidades recibidas y costes de un albarán.", "parameters": {"type": "object", "properties": {"albaran_id": {"type": "integer"}}, "required": ["albaran_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "listar_devoluciones_proveedor", "description": "Lista devoluciones a proveedor por proveedor, estado o resolución.", "parameters": {"type": "object", "properties": {"proveedor_id": {"type": "integer"}, "estado": {"type": "string"}, "resolucion": {"type": "string"}, "limite": {"type": "integer", "minimum": 1, "maximum": 100}}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_detalle_devolucion_proveedor", "description": "Obtiene motivo, resolución, albarán de origen y líneas de una devolución.", "parameters": {"type": "object", "properties": {"devolucion_id": {"type": "integer"}}, "required": ["devolucion_id"], "additionalProperties": False}}},
]


def _numero(valor) -> float:
    return float(valor or 0)


def _proveedor(proveedor) -> dict | None:
    return ({"id": proveedor.id, "nombre": proveedor.nombre, "cif": proveedor.cif} if proveedor else None)


def _pedido(pedido: PedidoCompra) -> dict:
    return {"id": pedido.id, "numero": pedido.numero, "estado": pedido.estado,
            "fecha": pedido.fecha.isoformat() if pedido.fecha else None,
            "fecha_envio": pedido.fecha_envio.isoformat() if pedido.fecha_envio else None,
            "fecha_recepcion": pedido.fecha_recepcion.isoformat() if pedido.fecha_recepcion else None,
            "subtotal": _numero(pedido.subtotal), "iva_total": _numero(pedido.iva_total),
            "total": _numero(pedido.total), "proveedor": _proveedor(pedido.proveedor)}


def _albaran(albaran: AlbaranProveedor) -> dict:
    return {"id": albaran.id, "numero_interno": albaran.numero_interno,
            "numero_proveedor": albaran.numero_proveedor, "fecha": albaran.fecha.isoformat() if albaran.fecha else None,
            "estado": albaran.estado, "pedido_compra_id": albaran.pedido_compra_id,
            "proveedor": _proveedor(albaran.proveedor)}


def _limite(valor: int, defecto: int = 50) -> int:
    return max(1, min(int(valor or defecto), 100))


def _query_pedidos(db: Session):
    return db.query(PedidoCompra).options(selectinload(PedidoCompra.proveedor))


def buscar_pedido_compra(db: Session, texto: str) -> list[dict]:
    texto = (texto or "").strip()
    if not texto:
        return []
    patron = f"%{texto}%"
    pedidos = (_query_pedidos(db).filter(or_(PedidoCompra.numero.ilike(patron), PedidoCompra.estado.ilike(patron)))
               .order_by(PedidoCompra.fecha.desc(), PedidoCompra.id.desc()).limit(30).all())
    return [_pedido(pedido) for pedido in pedidos]


def listar_pedidos_compra(db: Session, proveedor_id: int | None = None, estado: str | None = None, limite: int = 50) -> list[dict]:
    query = _query_pedidos(db)
    if proveedor_id:
        query = query.filter(PedidoCompra.proveedor_id == proveedor_id)
    if estado:
        query = query.filter(PedidoCompra.estado == estado.upper())
    return [_pedido(pedido) for pedido in query.order_by(PedidoCompra.fecha.desc(), PedidoCompra.id.desc()).limit(_limite(limite)).all()]


def obtener_detalle_pedido_compra(db: Session, pedido_id: int | None) -> dict:
    if not pedido_id:
        return {"encontrado": False}
    pedido = (_query_pedidos(db).options(selectinload(PedidoCompra.lineas)).filter(PedidoCompra.id == pedido_id).first())
    if pedido is None:
        return {"encontrado": False}
    resultado = _pedido(pedido)
    resultado.update({"encontrado": True, "observaciones": pedido.observaciones, "lineas": [
        {"id": linea.id, "articulo_stock_id": linea.articulo_stock_id, "referencia": linea.referencia,
         "descripcion": linea.descripcion, "cantidad_pedida": _numero(linea.cantidad_pedida),
         "cantidad_recibida": _numero(linea.cantidad_recibida),
         "cantidad_pendiente": max(0, _numero(linea.cantidad_pedida) - _numero(linea.cantidad_recibida)),
         "coste_unitario": _numero(linea.coste_unitario), "iva": _numero(linea.iva), "total": _numero(linea.total)}
        for linea in pedido.lineas]})
    return resultado


def _query_albaranes(db: Session):
    return db.query(AlbaranProveedor).options(selectinload(AlbaranProveedor.proveedor))


def buscar_albaran_proveedor(db: Session, texto: str) -> list[dict]:
    texto = (texto or "").strip()
    if not texto:
        return []
    patron = f"%{texto}%"
    albaranes = (_query_albaranes(db).filter(or_(AlbaranProveedor.numero_interno.ilike(patron), AlbaranProveedor.numero_proveedor.ilike(patron)))
                 .order_by(AlbaranProveedor.fecha.desc(), AlbaranProveedor.id.desc()).limit(30).all())
    return [_albaran(albaran) for albaran in albaranes]


def listar_albaranes_proveedor(db: Session, proveedor_id: int | None = None, limite: int = 50) -> list[dict]:
    query = _query_albaranes(db)
    if proveedor_id:
        query = query.filter(AlbaranProveedor.proveedor_id == proveedor_id)
    return [_albaran(albaran) for albaran in query.order_by(AlbaranProveedor.fecha.desc(), AlbaranProveedor.id.desc()).limit(_limite(limite)).all()]


def obtener_detalle_albaran_proveedor(db: Session, albaran_id: int | None) -> dict:
    if not albaran_id:
        return {"encontrado": False}
    albaran = (_query_albaranes(db).options(selectinload(AlbaranProveedor.pedido_compra),
        selectinload(AlbaranProveedor.lineas).selectinload(LineaAlbaranProveedor.articulo))
        .filter(AlbaranProveedor.id == albaran_id).first())
    if albaran is None:
        return {"encontrado": False}
    resultado = _albaran(albaran)
    resultado.update({"encontrado": True, "observaciones": albaran.observaciones,
        "pedido_compra": ({"id": albaran.pedido_compra.id, "numero": albaran.pedido_compra.numero, "estado": albaran.pedido_compra.estado} if albaran.pedido_compra else None),
        "lineas": [{"id": linea.id, "articulo_stock_id": linea.articulo_stock_id,
                    "referencia": linea.articulo.referencia if linea.articulo else None,
                    "articulo": linea.articulo.nombre if linea.articulo else None,
                    "cantidad_recibida": _numero(linea.cantidad_recibida), "coste_unitario": _numero(linea.coste_unitario)} for linea in albaran.lineas]})
    return resultado


def _devolucion(devolucion: DevolucionProveedor) -> dict:
    return {"id": devolucion.id, "numero": devolucion.numero, "fecha": devolucion.fecha.isoformat() if devolucion.fecha else None,
            "estado": devolucion.estado, "resolucion": devolucion.resolucion, "motivo": devolucion.motivo,
            "proveedor": _proveedor(devolucion.proveedor), "albaran_origen": devolucion.albaran_origen.numero_interno if devolucion.albaran_origen else None}


def listar_devoluciones_proveedor(db: Session, proveedor_id: int | None = None, estado: str | None = None, resolucion: str | None = None, limite: int = 50) -> list[dict]:
    query = db.query(DevolucionProveedor).options(selectinload(DevolucionProveedor.proveedor), selectinload(DevolucionProveedor.albaran_origen))
    if proveedor_id:
        query = query.filter(DevolucionProveedor.proveedor_id == proveedor_id)
    if estado:
        query = query.filter(DevolucionProveedor.estado == estado.upper())
    if resolucion:
        query = query.filter(DevolucionProveedor.resolucion == resolucion.upper())
    return [_devolucion(devolucion) for devolucion in query.order_by(DevolucionProveedor.fecha.desc(), DevolucionProveedor.id.desc()).limit(_limite(limite)).all()]


def obtener_detalle_devolucion_proveedor(db: Session, devolucion_id: int | None) -> dict:
    if not devolucion_id:
        return {"encontrada": False}
    devolucion = (db.query(DevolucionProveedor).options(selectinload(DevolucionProveedor.proveedor), selectinload(DevolucionProveedor.albaran_origen),
        selectinload(DevolucionProveedor.lineas).selectinload(LineaDevolucionProveedor.articulo))
        .filter(DevolucionProveedor.id == devolucion_id).first())
    if devolucion is None:
        return {"encontrada": False}
    resultado = _devolucion(devolucion)
    resultado.update({"encontrada": True, "observaciones": devolucion.observaciones,
        "albaran_origen": ({"id": devolucion.albaran_origen.id, "numero_interno": devolucion.albaran_origen.numero_interno, "numero_proveedor": devolucion.albaran_origen.numero_proveedor} if devolucion.albaran_origen else None),
        "lineas": [{"id": linea.id, "articulo_stock_id": linea.articulo_stock_id,
                    "referencia": linea.articulo.referencia if linea.articulo else None, "articulo": linea.articulo.nombre if linea.articulo else None,
                    "cantidad": _numero(linea.cantidad), "linea_albaran_id": linea.linea_albaran_id} for linea in devolucion.lineas]})
    return resultado
"""Herramientas IA de consulta de proveedores, pedidos y compras."""
