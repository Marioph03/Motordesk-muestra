from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from app.models.orden_interna import OrdenInterna, LineaOrdenInterna
from app.models.articulo_stock import ArticuloStock
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.services.stock_service import StockService

class OrdenInternaService:
    @staticmethod
    def listar(db: Session):
        return db.query(OrdenInterna).options(joinedload(OrdenInterna.lineas)).order_by(OrdenInterna.fecha_apertura.desc()).all()
    @staticmethod
    def obtener(db: Session, orden_id: int):
        orden = db.query(OrdenInterna).options(joinedload(OrdenInterna.lineas)).filter(OrdenInterna.id == orden_id).first()
        if not orden: raise ValueError("Orden interna no encontrada")
        return orden
    @staticmethod
    def crear(db: Session, datos):
        ultimo = db.query(OrdenInterna).order_by(OrdenInterna.id.desc()).first()
        vehiculo = db.get(Vehiculo, datos.vehiculo_id) if datos.vehiculo_id else None
        if datos.vehiculo_id and not vehiculo: raise ValueError("Vehículo no encontrado")
        referencia = f"{vehiculo.matricula} · {vehiculo.marca} {vehiculo.modelo}" if vehiculo else (datos.referencia_activo or "").strip() or None
        orden = OrdenInterna(numero=f"OI-{datetime.now():%Y}-{(ultimo.id + 1 if ultimo else 1):06d}", titulo=datos.titulo.strip(), categoria=datos.categoria, vehiculo_id=vehiculo.id if vehiculo else None, referencia_activo=referencia, descripcion=datos.descripcion.strip(), responsable_id=datos.responsable_id)
        if orden.responsable_id and not db.get(Usuario, orden.responsable_id): raise ValueError("Responsable no encontrado")
        db.add(orden); db.commit(); db.refresh(orden); return orden
    @staticmethod
    def anadir_linea(db: Session, orden_id: int, datos):
        orden = OrdenInternaService.obtener(db, orden_id)
        if orden.estado == "CERRADA": raise ValueError("La orden interna está cerrada")
        articulo = db.get(ArticuloStock, datos.articulo_stock_id) if datos.articulo_stock_id else None
        if datos.articulo_stock_id and not articulo: raise ValueError("Producto no encontrado")
        linea = LineaOrdenInterna(orden_interna_id=orden.id, tipo=datos.tipo, articulo_stock_id=articulo.id if articulo else None, referencia=articulo.referencia if articulo else None, descripcion=(articulo.nombre if articulo else datos.descripcion.strip()), cantidad=datos.cantidad, coste_unitario=(articulo.coste if articulo else datos.coste_unitario))
        db.add(linea); db.flush(); OrdenInternaService._recalcular(orden); db.commit(); db.refresh(linea); return linea
    @staticmethod
    def borrar_linea(db: Session, orden_id: int, linea_id: int):
        orden = OrdenInternaService.obtener(db, orden_id)
        if orden.estado == "CERRADA": raise ValueError("La orden interna está cerrada")
        linea = db.query(LineaOrdenInterna).filter_by(id=linea_id, orden_interna_id=orden.id).first()
        if not linea: raise ValueError("Línea no encontrada")
        db.delete(linea); db.flush(); OrdenInternaService._recalcular(orden); db.commit()
    @staticmethod
    def cerrar(db: Session, orden_id: int):
        orden = OrdenInternaService.obtener(db, orden_id)
        if orden.estado == "CERRADA": return orden
        for linea in orden.lineas:
            if linea.tipo == "PIEZA" and linea.articulo_stock_id:
                # El movimiento no puede enlazarse a ordenes_reparacion: esta
                # orden es interna, pero el consumo de existencias sí es real.
                StockService.consumir_desde_orden(db, linea.articulo_stock_id, Decimal(linea.cantidad), None, commit=False)
        orden.estado = "CERRADA"; orden.fecha_cierre = datetime.utcnow(); db.commit(); db.refresh(orden); return orden
    @staticmethod
    def _recalcular(orden):
        orden.coste_total = sum((Decimal(linea.cantidad) * Decimal(linea.coste_unitario) for linea in orden.lineas), Decimal("0"))
