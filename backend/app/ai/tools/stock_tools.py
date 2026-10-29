from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models.articulo_stock import ArticuloStock
from app.models.movimiento_stock import MovimientoStock


STOCK_TOOLS = [
    {"type": "function", "function": {"name": "buscar_articulo_stock", "description": "Busca artículos o recambios por referencia, nombre, descripción, marca o categoría; útil para consultar existencias.", "parameters": {"type": "object", "properties": {"texto": {"type": "string"}, "solo_activos": {"type": "boolean"}}, "required": ["texto"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_detalle_stock", "description": "Obtiene stock, precios, ubicación y proveedor habitual de un artículo.", "parameters": {"type": "object", "properties": {"articulo_id": {"type": "integer"}}, "required": ["articulo_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "listar_stock_bajo", "description": "Lista artículos activos con stock igual o inferior al mínimo.", "parameters": {"type": "object", "properties": {"limite": {"type": "integer", "minimum": 1, "maximum": 100}}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "listar_articulos_sin_stock", "description": "Lista artículos activos sin existencias disponibles.", "parameters": {"type": "object", "properties": {"limite": {"type": "integer", "minimum": 1, "maximum": 100}}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_movimientos_stock", "description": "Obtiene entradas, salidas, consumos de orden, devoluciones y ajustes de un artículo.", "parameters": {"type": "object", "properties": {"articulo_id": {"type": "integer"}, "limite": {"type": "integer", "minimum": 1, "maximum": 100}}, "required": ["articulo_id"], "additionalProperties": False}}},
]


def _numero(valor) -> float:
    return float(valor or 0)


def _serializar(articulo: ArticuloStock) -> dict:
    stock_actual, stock_minimo = _numero(articulo.stock_actual), _numero(articulo.stock_minimo)
    proveedor = None
    if articulo.proveedor_habitual:
        proveedor = {"id": articulo.proveedor_habitual.id, "nombre": articulo.proveedor_habitual.nombre}
    return {
        "id": articulo.id, "referencia": articulo.referencia, "nombre": articulo.nombre,
        "marca": articulo.marca, "categoria": articulo.categoria, "ubicacion": articulo.ubicacion,
        "stock_actual": stock_actual, "stock_minimo": stock_minimo,
        "bajo_minimo": stock_actual <= stock_minimo, "sin_stock": stock_actual <= 0,
        "activo": bool(articulo.activo), "proveedor_habitual": proveedor,
    }


def _query(db: Session):
    return db.query(ArticuloStock).options(selectinload(ArticuloStock.proveedor_habitual))


def _limite(limite: int, defecto: int = 50) -> int:
    return max(1, min(int(limite or defecto), 100))


def buscar_articulo_stock(db: Session, texto: str, solo_activos: bool = True) -> list[dict]:
    texto = (texto or "").strip()
    if not texto:
        return []
    patron = f"%{texto}%"
    query = _query(db).filter(or_(ArticuloStock.referencia.ilike(patron), ArticuloStock.nombre.ilike(patron),
        ArticuloStock.descripcion.ilike(patron), ArticuloStock.marca.ilike(patron), ArticuloStock.categoria.ilike(patron)))
    if solo_activos:
        query = query.filter(ArticuloStock.activo.is_(True))
    return [_serializar(articulo) for articulo in query.order_by(ArticuloStock.nombre.asc(), ArticuloStock.id.asc()).limit(30).all()]


def obtener_detalle_stock(db: Session, articulo_id: int | None) -> dict:
    if not articulo_id:
        return {"encontrado": False}
    articulo = _query(db).filter(ArticuloStock.id == articulo_id).first()
    if articulo is None:
        return {"encontrado": False}
    resultado = _serializar(articulo)
    resultado.update({"encontrado": True, "descripcion": articulo.descripcion, "coste": _numero(articulo.coste),
                      "precio_venta": _numero(articulo.precio_venta), "iva": _numero(articulo.iva)})
    return resultado


def listar_stock_bajo(db: Session, limite: int = 50) -> list[dict]:
    articulos = (_query(db).filter(ArticuloStock.activo.is_(True), ArticuloStock.stock_actual <= ArticuloStock.stock_minimo)
                .order_by(ArticuloStock.stock_actual.asc(), ArticuloStock.nombre.asc()).limit(_limite(limite)).all())
    return [_serializar(articulo) for articulo in articulos]


def listar_articulos_sin_stock(db: Session, limite: int = 50) -> list[dict]:
    articulos = (_query(db).filter(ArticuloStock.activo.is_(True), ArticuloStock.stock_actual <= 0)
                .order_by(ArticuloStock.nombre.asc()).limit(_limite(limite)).all())
    return [_serializar(articulo) for articulo in articulos]


def obtener_movimientos_stock(db: Session, articulo_id: int | None, limite: int = 30) -> list[dict]:
    if not articulo_id:
        return []
    movimientos = (db.query(MovimientoStock).options(selectinload(MovimientoStock.orden))
                   .filter(MovimientoStock.articulo_id == articulo_id)
                   .order_by(MovimientoStock.fecha.desc(), MovimientoStock.id.desc()).limit(_limite(limite, 30)).all())
    return [{
        "id": movimiento.id, "tipo": movimiento.tipo, "cantidad": _numero(movimiento.cantidad),
        "stock_anterior": _numero(movimiento.stock_anterior), "stock_resultante": _numero(movimiento.stock_resultante),
        "motivo": movimiento.motivo, "fecha": movimiento.fecha.isoformat() if movimiento.fecha else None,
        "orden": ({"id": movimiento.orden.id, "numero": movimiento.orden.numero} if movimiento.orden else None),
    } for movimiento in movimientos]
"""Herramientas IA de consulta de existencias y artículos de almacén."""
