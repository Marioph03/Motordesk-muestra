from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.articulo_stock import ArticuloStock
from app.models.proveedor import Proveedor


PROVEEDORES_TOOLS = [
    {"type": "function", "function": {"name": "buscar_proveedor", "description": "Busca proveedores por nombre, CIF, teléfono, correo o dirección.", "parameters": {"type": "object", "properties": {"texto": {"type": "string"}, "solo_activos": {"type": "boolean"}}, "required": ["texto"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_detalle_proveedor", "description": "Obtiene datos de contacto de un proveedor.", "parameters": {"type": "object", "properties": {"proveedor_id": {"type": "integer"}}, "required": ["proveedor_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "listar_proveedores", "description": "Lista proveedores activos o todos los proveedores.", "parameters": {"type": "object", "properties": {"solo_activos": {"type": "boolean"}, "limite": {"type": "integer", "minimum": 1, "maximum": 100}}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_articulos_proveedor", "description": "Obtiene artículos cuyo proveedor habitual es el proveedor indicado.", "parameters": {"type": "object", "properties": {"proveedor_id": {"type": "integer"}, "solo_activos": {"type": "boolean"}}, "required": ["proveedor_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "obtener_reposicion_proveedor", "description": "Obtiene artículos bajo mínimo que habría que pedir a un proveedor habitual.", "parameters": {"type": "object", "properties": {"proveedor_id": {"type": "integer"}}, "required": ["proveedor_id"], "additionalProperties": False}}},
]


def _numero(valor) -> float:
    return float(valor or 0)


def _proveedor(proveedor: Proveedor) -> dict:
    return {"id": proveedor.id, "nombre": proveedor.nombre, "cif": proveedor.cif,
            "telefono": proveedor.telefono, "email": proveedor.email,
            "direccion": proveedor.direccion, "activo": bool(proveedor.activo)}


def _articulo(articulo: ArticuloStock) -> dict:
    actual, minimo = _numero(articulo.stock_actual), _numero(articulo.stock_minimo)
    return {"id": articulo.id, "referencia": articulo.referencia, "nombre": articulo.nombre,
            "marca": articulo.marca, "categoria": articulo.categoria, "ubicacion": articulo.ubicacion,
            "stock_actual": actual, "stock_minimo": minimo, "bajo_minimo": actual <= minimo,
            "sin_stock": actual <= 0, "coste": _numero(articulo.coste), "precio_venta": _numero(articulo.precio_venta)}


def _limite(valor: int, defecto: int = 50) -> int:
    return max(1, min(int(valor or defecto), 100))


def buscar_proveedor(db: Session, texto: str, solo_activos: bool = True) -> list[dict]:
    texto = (texto or "").strip()
    if not texto:
        return []
    patron = f"%{texto}%"
    query = db.query(Proveedor).filter(or_(Proveedor.nombre.ilike(patron), Proveedor.cif.ilike(patron),
        Proveedor.telefono.ilike(patron), Proveedor.email.ilike(patron), Proveedor.direccion.ilike(patron)))
    if solo_activos:
        query = query.filter(Proveedor.activo.is_(True))
    return [_proveedor(proveedor) for proveedor in query.order_by(Proveedor.nombre.asc(), Proveedor.id.asc()).limit(30).all()]


def obtener_detalle_proveedor(db: Session, proveedor_id: int | None) -> dict:
    if not proveedor_id:
        return {"encontrado": False}
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if proveedor is None:
        return {"encontrado": False}
    resultado = _proveedor(proveedor)
    resultado["encontrado"] = True
    return resultado


def listar_proveedores(db: Session, solo_activos: bool = True, limite: int = 50) -> list[dict]:
    query = db.query(Proveedor)
    if solo_activos:
        query = query.filter(Proveedor.activo.is_(True))
    return [_proveedor(proveedor) for proveedor in query.order_by(Proveedor.nombre.asc(), Proveedor.id.asc()).limit(_limite(limite)).all()]


def obtener_articulos_proveedor(db: Session, proveedor_id: int | None, solo_activos: bool = True) -> list[dict]:
    if not proveedor_id:
        return []
    query = db.query(ArticuloStock).filter(ArticuloStock.proveedor_habitual_id == proveedor_id)
    if solo_activos:
        query = query.filter(ArticuloStock.activo.is_(True))
    return [_articulo(articulo) for articulo in query.order_by(ArticuloStock.nombre.asc(), ArticuloStock.id.asc()).limit(100).all()]


def obtener_reposicion_proveedor(db: Session, proveedor_id: int | None) -> list[dict]:
    if not proveedor_id:
        return []
    articulos = (db.query(ArticuloStock).filter(ArticuloStock.proveedor_habitual_id == proveedor_id,
        ArticuloStock.activo.is_(True), ArticuloStock.stock_actual <= ArticuloStock.stock_minimo)
        .order_by(ArticuloStock.stock_actual.asc(), ArticuloStock.nombre.asc()).limit(100).all())
    resultado = []
    for articulo in articulos:
        datos = _articulo(articulo)
        datos["unidades_para_minimo"] = max(0, datos["stock_minimo"] - datos["stock_actual"])
        resultado.append(datos)
    return resultado
"""Herramientas IA para localizar proveedores sin modificar su catálogo."""
