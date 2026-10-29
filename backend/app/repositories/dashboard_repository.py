from datetime import date, datetime, time

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.vehiculo import Vehiculo
from app.models.orden_reparacion import EstadoReparacion, OrdenReparacion
from app.models.factura import Factura
from app.models.articulo_stock import ArticuloStock
from app.models.cita import Cita, EstadoCita
from app.models.factura import EstadoCobro



class DashboardRepository:

    _MESES_CORTOS = (
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
    )

    @staticmethod
    def _primer_dia_mes_anterior(fecha: date) -> date:
        if fecha.month == 1:
            return date(fecha.year - 1, 12, 1)

        return date(fecha.year, fecha.month - 1, 1)

    @staticmethod
    def get_stats(
        db: Session
    ):

        hoy = date.today()

        clientes = db.query(
            func.count(Cliente.id)
        ).scalar()

        vehiculos = db.query(
            func.count(Vehiculo.id)
        ).scalar()

        ordenes_abiertas = db.query(
            func.count(OrdenReparacion.id)
        ).filter(
            OrdenReparacion.estado == EstadoReparacion.ABIERTA.value
        ).scalar()

        ordenes_cerradas = db.query(
            func.count(OrdenReparacion.id)
        ).filter(
            OrdenReparacion.estado == EstadoReparacion.CERRADA.value
        ).scalar()

        presupuestos = db.query(
            func.count(Factura.id)
        ).filter(
            Factura.tipo_documento == "PRESUPUESTO"
        ).scalar()

        facturas = db.query(
            func.count(Factura.id)
        ).filter(
            Factura.tipo_documento == "FACTURA"
        ).scalar()

        stock_actual = db.query(
            func.coalesce(
                func.sum(ArticuloStock.stock_actual),
                0
            )
        ).filter(
            ArticuloStock.activo.is_(True)
        ).scalar()

        stock_bajo = db.query(
            func.count(ArticuloStock.id)
        ).filter(
            ArticuloStock.activo.is_(True),
            ArticuloStock.stock_actual <= ArticuloStock.stock_minimo
        ).scalar()

        inicio_hoy = datetime.combine(hoy, time.min)
        fin_hoy = datetime.combine(hoy, time.max)

        citas_hoy = db.query(
            func.count(Cita.id)
        ).filter(
            Cita.fecha_inicio >= inicio_hoy,
            Cita.fecha_inicio <= fin_hoy,
            Cita.estado.notin_([
                EstadoCita.CANCELADA.value,
                EstadoCita.NO_PRESENTADO.value,
                EstadoCita.COMPLETADA.value
            ])
        ).scalar()

        cobros_pendientes = db.query(
            func.count(Factura.id)
        ).filter(
            Factura.tipo_documento == "FACTURA",
            Factura.estado == "EMITIDA",
            Factura.estado_cobro.in_([
                EstadoCobro.PENDIENTE.value,
                EstadoCobro.PARCIAL.value
            ])
        ).scalar()

        facturacion_mes = (
            db.query(
                func.sum(Factura.total)
            )
            .filter(
                Factura.tipo_documento == "FACTURA",
                Factura.estado == "EMITIDA",
                func.extract("month", Factura.fecha_emision) == hoy.month,
                func.extract("year", Factura.fecha_emision) == hoy.year,
            )
            .scalar()
            or 0
        )

        facturacion_anual = (
            db.query(
                func.sum(Factura.total)
            )
            .filter(
                Factura.tipo_documento == "FACTURA",
                Factura.estado == "EMITIDA",
                func.extract("year", Factura.fecha_emision) == hoy.year,
            )
            .scalar()
            or 0
        )

        # La gráfica conserva los seis meses, incluidos aquellos sin ventas.
        primer_mes = date(hoy.year, hoy.month, 1)
        for _ in range(5):
            primer_mes = (
                DashboardRepository
                ._primer_dia_mes_anterior(primer_mes)
            )

        meses = []
        for _ in range(6):
            meses.append(primer_mes)
            primer_mes = (
                date(primer_mes.year + 1, 1, 1)
                if primer_mes.month == 12
                else date(
                    primer_mes.year,
                    primer_mes.month + 1,
                    1
                )
            )

        inicio_grafica = datetime.combine(
            meses[0], datetime.min.time()
        )
        fin_grafica = datetime.combine(
            primer_mes, datetime.min.time()
        )

        importes_por_mes = {
            (int(anio), int(mes)): float(total or 0)
            for anio, mes, total in (
                db.query(
                    func.extract("year", Factura.fecha_emision),
                    func.extract("month", Factura.fecha_emision),
                    func.sum(Factura.total)
                )
                .filter(
                    Factura.tipo_documento == "FACTURA",
                    Factura.estado == "EMITIDA",
                    Factura.fecha_emision >= inicio_grafica,
                    Factura.fecha_emision < fin_grafica
                )
                .group_by(
                    func.extract("year", Factura.fecha_emision),
                    func.extract("month", Factura.fecha_emision)
                )
                .all()
            )
        }

        facturacion_ultimos_meses = [
            {
                "periodo": mes.isoformat(),
                "etiqueta": DashboardRepository._MESES_CORTOS[
                    mes.month - 1
                ],
                "total": importes_por_mes.get(
                    (mes.year, mes.month), 0
                )
            }
            for mes in meses
        ]

        ultimas_facturas = (
            db.query(Factura)
            .filter(
                Factura.tipo_documento == "FACTURA"
            )
            .order_by(
                Factura.fecha_emision.desc()
            )
            .limit(5)
            .all()
        )

        ultimas_ordenes = (
            db.query(OrdenReparacion)
            .order_by(
                OrdenReparacion.fecha_entrada.desc()
            )
            .limit(5)
            .all()
        )

        return {
            "clientes": clientes,
            "vehiculos": vehiculos,
            "ordenes_abiertas": ordenes_abiertas,
            "ordenes_cerradas": ordenes_cerradas,
            "presupuestos": presupuestos,
            "stock_actual": float(stock_actual),
            "stock_bajo": stock_bajo,
            "citas_hoy": citas_hoy,
            "cobros_pendientes": cobros_pendientes,
            "facturas": facturas,
            "facturacion_mes": float(facturacion_mes),
            "facturacion_anual": float(facturacion_anual),
            "facturacion_ultimos_meses": facturacion_ultimos_meses,
            "ultimas_facturas": [
                {
                    "id": f.id,
                    "numero": f.numero,
                    "estado": f.estado,
                    "total": float(f.total),
                    "fecha_emision": f.fecha_emision,
                    "cliente": {
                        "nombre": f.cliente.nombre,
                        "apellidos": f.cliente.apellidos
                    } if f.cliente else None
                }
                for f in ultimas_facturas
            ],
            "ultimas_ordenes": [
                {
                    "id": o.id,
                    "numero": o.numero,
                    "estado": o.estado,
                    "fecha_entrada": o.fecha_entrada,
                    "descripcion_averia": o.descripcion_averia,
                    "importe_total": float(o.importe_total),
                    "vehiculo": {
                        "marca": o.vehiculo.marca,
                        "modelo": o.vehiculo.modelo,
                        "matricula": o.vehiculo.matricula
                    } if o.vehiculo else None
                }
                for o in ultimas_ordenes
            ],
        }
        
    
"""Consultas agregadas de solo lectura para los indicadores del Dashboard."""
