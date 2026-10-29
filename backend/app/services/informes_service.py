"""Agregados de negocio para informes operativos, económicos y de personal."""

from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from app.models.orden_reparacion import EstadoReparacion
from app.models.factura import EstadoFactura, Factura
from app.models.factura_proveedor import FacturaProveedor
from app.repositories.factura_repository import FacturaRepository
from app.models.movimiento_stock import TipoMovimientoStock
from app.repositories.movimiento_stock_repository import (
    MovimientoStockRepository,
)
from app.models.pedido_compra import EstadoPedidoCompra
from app.repositories.pedido_compra_repository import PedidoCompraRepository
from app.repositories.ausencia_personal_repository import (
    AusenciaPersonalRepository,
)
from app.repositories.cita_repository import CitaRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.repositories.orden_reparacion_repository import (
    OrdenReparacionRepository,
)


class InformesService:
    """Construye un resumen consistente para un rango sin alterar datos fuente."""


    @staticmethod
    def resumen_general(
        db: Session,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        cliente_id: int | None = None,
        proveedor_id: int | None = None,
        gasto_id: int | None = None,
    ):
        if fecha_fin <= fecha_inicio:
            raise ValueError(
                "La fecha final debe ser posterior a la inicial"
            )

        # En informes de taller importa cuándo entró el vehículo, no cuándo se
        # creó internamente el registro.
        ordenes = OrdenReparacionRepository.get_en_rango(
            db,
            fecha_inicio,
            fecha_fin,
        )

        cerradas = sum(
            1
            for orden in ordenes
            if orden.estado == EstadoReparacion.CERRADA.value
        )
        facturadas = sum(
            1
            for orden in ordenes
            if orden.estado == EstadoReparacion.FACTURADA.value
        )
        garantias = sum(1 for orden in ordenes if orden.tipo == "GA")
        presupuestos = sum(1 for orden in ordenes if orden.tipo == "PR")

        estados_finales = {
            EstadoReparacion.CERRADA.value,
            EstadoReparacion.FACTURADA.value,
            # Compatibilidad con registros históricos si existen.
            "Cancelada",
        }
        en_curso = sum(
            1
            for orden in ordenes
            if orden.estado not in estados_finales
        )

        motivos = [
            orden.descripcion_averia.strip()
            for orden in ordenes
            if orden.descripcion_averia and orden.descripcion_averia.strip()
        ]
        trabajos_frecuentes = [
            {
                "descripcion": descripcion,
                "total": total,
            }
            for descripcion, total in Counter(motivos).most_common(10)
        ]

        facturas = FacturaRepository.get_emitidas_en_rango(
            db,
            fecha_inicio,
            fecha_fin,
        )
        if cliente_id:
            facturas = [factura for factura in facturas if factura.cliente_id == cliente_id]
        # Un borrador tiene fecha técnica de creación, pero no representa
        # facturación real. Solo cuentan las facturas emitidas.
        facturas_validas = [
            factura
            for factura in facturas
            if factura.estado == EstadoFactura.EMITIDA.value
        ]
        facturas_anuladas = sum(
            1
            for factura in facturas
            if factura.estado == EstadoFactura.ANULADA.value
        )
        total_facturado = sum(
            (Decimal(factura.total) for factura in facturas_validas),
            Decimal("0.00"),
        )
        facturas_emitidas = len(facturas_validas)
        ticket_medio = (
            (total_facturado / Decimal(facturas_emitidas)).quantize(
                Decimal("0.01")
            )
            if facturas_emitidas > 0
            else Decimal("0.00")
        )

        facturacion_por_dia = defaultdict(lambda: Decimal("0.00"))
        for factura in facturas_validas:
            facturacion_por_dia[factura.fecha_emision.date()] += Decimal(
                factura.total
            )
        evolucion_diaria = [
            {
                "fecha": fecha,
                "total": total,
            }
            for fecha, total in sorted(facturacion_por_dia.items())
        ]

        # IVA repercutido (ventas emitidas) menos IVA soportado (facturas de
        # proveedor). Las fechas usan el mismo intervalo exclusivo del informe.
        iva_repercutido = sum(
            (Decimal(factura.cuota_iva or 0) for factura in facturas_validas),
            Decimal("0.00"),
        )
        consulta_facturas_proveedor = db.query(FacturaProveedor).filter(
            FacturaProveedor.fecha_factura >= fecha_inicio.date(),
            FacturaProveedor.fecha_factura < fecha_fin.date(),
        )
        if proveedor_id:
            consulta_facturas_proveedor = consulta_facturas_proveedor.filter(FacturaProveedor.proveedor_id == proveedor_id)
        if gasto_id:
            consulta_facturas_proveedor = consulta_facturas_proveedor.filter(FacturaProveedor.id == gasto_id)
        facturas_proveedor = consulta_facturas_proveedor.all()
        iva_soportado = sum(
            (Decimal(factura.iva or 0) for factura in facturas_proveedor),
            Decimal("0.00"),
        )

        movimientos_stock = MovimientoStockRepository.get_en_rango(
            db,
            fecha_inicio,
            fecha_fin,
        )
        unidades_consumidas = sum(
            (
                Decimal(movimiento.cantidad)
                for movimiento in movimientos_stock
                if movimiento.tipo == TipoMovimientoStock.CONSUMO_ORDEN.value
            ),
            Decimal("0.00"),
        )
        entradas_compra = sum(
            (
                Decimal(movimiento.cantidad)
                for movimiento in movimientos_stock
                if movimiento.tipo == TipoMovimientoStock.ENTRADA_COMPRA.value
            ),
            Decimal("0.00"),
        )
        ajustes_positivos = sum(
            (
                Decimal(movimiento.cantidad)
                for movimiento in movimientos_stock
                if movimiento.tipo == TipoMovimientoStock.AJUSTE_POSITIVO.value
            ),
            Decimal("0.00"),
        )
        ajustes_negativos = sum(
            (
                Decimal(movimiento.cantidad)
                for movimiento in movimientos_stock
                if movimiento.tipo == TipoMovimientoStock.AJUSTE_NEGATIVO.value
            ),
            Decimal("0.00"),
        )
        ranking_stock = (
            MovimientoStockRepository.get_mas_consumidos_en_rango(
                db,
                fecha_inicio,
                fecha_fin,
                limite=10,
            )
        )
        articulos_mas_consumidos = [
            {
                "articulo_id": fila.articulo_id,
                "referencia": fila.referencia,
                "nombre": fila.nombre,
                "cantidad_consumida": fila.cantidad_consumida,
            }
            for fila in ranking_stock
        ]

        pedidos = PedidoCompraRepository.get_en_rango(
            db,
            fecha_inicio,
            fecha_fin,
        )
        if proveedor_id:
            pedidos = [pedido for pedido in pedidos if pedido.proveedor_id == proveedor_id]
        pedidos_recibidos = sum(
            1
            for pedido in pedidos
            if pedido.estado == EstadoPedidoCompra.RECIBIDO.value
        )
        pedidos_parciales = sum(
            1
            for pedido in pedidos
            if pedido.estado == EstadoPedidoCompra.RECIBIDO_PARCIAL.value
        )
        pedidos_cancelados = sum(
            1
            for pedido in pedidos
            if pedido.estado == EstadoPedidoCompra.CANCELADO.value
        )
        estados_compra_validos = {
            EstadoPedidoCompra.ENVIADO.value,
            EstadoPedidoCompra.RECIBIDO_PARCIAL.value,
            EstadoPedidoCompra.RECIBIDO.value,
        }
        pedidos_validos = [
            pedido
            for pedido in pedidos
            if pedido.estado in estados_compra_validos
        ]
        total_compras = sum(
            (Decimal(pedido.total) for pedido in pedidos_validos),
            Decimal("0.00"),
        )
        ticket_medio_compra = (
            (total_compras / Decimal(len(pedidos_validos))).quantize(
                Decimal("0.01")
            )
            if pedidos_validos
            else Decimal("0.00")
        )
        ranking_proveedores = (
            PedidoCompraRepository.get_proveedores_mayor_volumen(
                db,
                fecha_inicio,
                fecha_fin,
                limite=10,
            )
        )
        proveedores_top = [
            {
                "proveedor_id": fila.proveedor_id,
                "nombre": fila.nombre,
                "pedidos": fila.pedidos,
                "total_compras": fila.total_compras,
            }
            for fila in ranking_proveedores
        ]

        garantias_informe = OrdenReparacionRepository.get_garantias_en_rango(
            db,
            fecha_inicio,
            fecha_fin,
        )
        garantias_abiertas = sum(
            1
            for garantia in garantias_informe
            if garantia.estado == EstadoReparacion.GARANTIA_ABIERTA.value
        )
        garantias_en_revision = sum(
            1
            for garantia in garantias_informe
            if garantia.estado == EstadoReparacion.GARANTIA_REVISION.value
        )
        garantias_aprobadas = sum(
            1
            for garantia in garantias_informe
            if garantia.estado == EstadoReparacion.GARANTIA_APROBADA.value
        )
        garantias_rechazadas = sum(
            1
            for garantia in garantias_informe
            if garantia.estado == EstadoReparacion.GARANTIA_RECHAZADA.value
        )
        garantias_en_reparacion = sum(
            1
            for garantia in garantias_informe
            if garantia.estado == EstadoReparacion.GARANTIA_REPARACION.value
        )
        total_garantias_resueltas = sum(
            1
            for garantia in garantias_informe
            if garantia.estado == EstadoReparacion.GARANTIA_RESUELTA.value
        )
        garantias_resueltas_con_fecha = [
            garantia
            for garantia in garantias_informe
            if (
                garantia.estado == EstadoReparacion.GARANTIA_RESUELTA.value
                and garantia.fecha_resolucion_garantia is not None
            )
        ]
        tiempo_medio_resolucion_horas = (
            sum(
                (
                    garantia.fecha_resolucion_garantia
                    - garantia.fecha_entrada
                ).total_seconds()
                for garantia in garantias_resueltas_con_fecha
            )
            / len(garantias_resueltas_con_fecha)
            / 3600
            if garantias_resueltas_con_fecha
            else 0.0
        )

        usuarios_activos = UsuarioRepository.get_activos(db)
        detalle_personal = []
        for usuario in usuarios_activos:
            ordenes_asignadas = (
                OrdenReparacionRepository.count_por_usuario_en_rango(
                    db,
                    usuario.id,
                    fecha_inicio,
                    fecha_fin,
                )
            )
            citas_asignadas = CitaRepository.count_por_usuario_en_rango(
                db,
                usuario.id,
                fecha_inicio,
                fecha_fin,
            )
            ausencias = AusenciaPersonalRepository.get_usuario_en_rango(
                db,
                usuario.id,
                fecha_inicio,
                fecha_fin,
            )
            dias_ausencia = 0.0
            for ausencia in ausencias:
                inicio = max(ausencia.fecha_inicio, fecha_inicio)
                fin = min(ausencia.fecha_fin, fecha_fin)
                if fin > inicio:
                    dias_ausencia += (
                        fin - inicio
                    ).total_seconds() / 86_400

            detalle_personal.append({
                "usuario_id": usuario.id,
                "nombre": ", ".join(parte for parte in [usuario.apellidos or "", usuario.nombre or ""] if parte),
                "rol": usuario.rol,
                "ordenes_asignadas": ordenes_asignadas,
                "citas_asignadas": citas_asignadas,
                "ausencias": len(ausencias),
                "dias_ausencia": round(dias_ausencia, 1),
                "actividad_total": ordenes_asignadas + citas_asignadas,
            })
        detalle_personal.sort(
            key=lambda item: item["actividad_total"],
            reverse=True,
        )

        return {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "ordenes": {
                "total": len(ordenes),
                "cerradas": cerradas,
                "facturadas": facturadas,
                "garantias": garantias,
                "presupuestos": presupuestos,
                "en_curso": en_curso,
                "trabajos_frecuentes": trabajos_frecuentes,
            },
            # Los siguientes bloques se alimentarán de sus módulos respectivos.
            "facturacion": {
                "facturas_emitidas": facturas_emitidas,
                "facturas_anuladas": facturas_anuladas,
                "total_facturado": total_facturado,
                "ticket_medio": ticket_medio,
                "evolucion_diaria": evolucion_diaria,
            },
            "stock": {
                "movimientos": len(movimientos_stock),
                "unidades_consumidas": unidades_consumidas,
                "entradas_compra": entradas_compra,
                "ajustes_positivos": ajustes_positivos,
                "ajustes_negativos": ajustes_negativos,
                "articulos_mas_consumidos": articulos_mas_consumidos,
            },
            "compras": {
                "pedidos": len(pedidos),
                "recibidos": pedidos_recibidos,
                "recibidos_parciales": pedidos_parciales,
                "cancelados": pedidos_cancelados,
                "total_compras": total_compras,
                "ticket_medio": ticket_medio_compra,
                "proveedores_top": proveedores_top,
            },
            "iva": {
                "iva_repercutido": iva_repercutido,
                "iva_soportado": iva_soportado,
                "diferencia": iva_repercutido - iva_soportado,
            },
            "garantias": {
                "total": len(garantias_informe),
                "abiertas": garantias_abiertas,
                "en_revision": garantias_en_revision,
                "aprobadas": garantias_aprobadas,
                "rechazadas": garantias_rechazadas,
                "en_reparacion": garantias_en_reparacion,
                "resueltas": total_garantias_resueltas,
                "tiempo_medio_resolucion_horas": round(
                    tiempo_medio_resolucion_horas,
                    2,
                ),
                "tiempo_medio_resolucion_dias": round(
                    tiempo_medio_resolucion_horas / 24,
                    2,
                ),
            },
            "personal": {
                "usuarios_activos": len(usuarios_activos),
                "detalle": detalle_personal,
            },
        }

    @staticmethod
    def _validar_periodo(fecha_inicio: datetime, fecha_fin: datetime) -> None:
        if fecha_fin <= fecha_inicio:
            raise ValueError("La fecha final debe ser posterior a la inicial")

    @staticmethod
    def informe_facturacion(db: Session, fecha_inicio: datetime, fecha_fin: datetime, cliente_id: int | None = None):
        """Detalle económico de las facturas emitidas en el periodo."""
        InformesService._validar_periodo(fecha_inicio, fecha_fin)
        consulta = (
            db.query(Factura)
            .options(joinedload(Factura.cliente), joinedload(Factura.pagos))
            .filter(
                Factura.fecha_emision >= fecha_inicio,
                Factura.fecha_emision < fecha_fin,
                Factura.estado == EstadoFactura.EMITIDA.value,
            )
        )
        if cliente_id:
            consulta = consulta.filter(Factura.cliente_id == cliente_id)
        facturas = consulta.order_by(Factura.fecha_emision.asc(), Factura.id.asc()).all()
        filas = []
        base_total = iva_total = total = Decimal("0.00")
        for factura in facturas:
            cliente = factura.cliente
            etiquetas_pago = {
                "EFECTIVO": "Efectivo",
                "TARJETA": "Tarjeta",
                "TRANSFERENCIA": "Transferencia",
                "BIZUM": "Bizum",
                "OTRO": "Otro",
            }
            metodos_pago = list(dict.fromkeys(
                etiquetas_pago.get(pago.metodo_pago, pago.metodo_pago)
                for pago in factura.pagos
                if pago.metodo_pago
            ))
            base = Decimal(factura.base_imponible or 0)
            iva = Decimal(factura.cuota_iva or 0)
            importe_total = Decimal(factura.total or 0)
            base_total += base
            iva_total += iva
            total += importe_total
            filas.append({
                "fecha": factura.fecha_emision,
                "numero": factura.numero,
                "tercero": ", ".join(filter(None, [
                    getattr(cliente, "apellidos", None),
                    getattr(cliente, "nombre", None),
                ])) or "-",
                "nif": getattr(cliente, "dni", None) or "-",
                "metodo_pago": " + ".join(metodos_pago) if metodos_pago else "Pendiente",
                "base": base,
                "iva": iva,
                "total": importe_total,
            })
        return {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "filas": filas,
            "totales": {"documentos": len(filas), "base": base_total, "iva": iva_total, "total": total},
        }

    @staticmethod
    def informe_clientes(db: Session, fecha_inicio: datetime, fecha_fin: datetime, cliente_id: int | None = None):
        """Agrupa la facturación emitida por cliente."""
        detalle = InformesService.informe_facturacion(db, fecha_inicio, fecha_fin, cliente_id)
        agrupados = {}
        for factura in detalle["filas"]:
            clave = (factura["tercero"], factura["nif"])
            fila = agrupados.setdefault(clave, {
                "tercero": factura["tercero"], "nif": factura["nif"],
                "documentos": 0, "base": Decimal("0.00"),
                "iva": Decimal("0.00"), "total": Decimal("0.00"),
            })
            fila["documentos"] += 1
            fila["base"] += factura["base"]
            fila["iva"] += factura["iva"]
            fila["total"] += factura["total"]
        filas = sorted(agrupados.values(), key=lambda fila: (-fila["total"], fila["tercero"]))
        return {**detalle, "filas": filas, "totales": {**detalle["totales"], "documentos": len(filas)}}

    @staticmethod
    def informe_compras_gastos(db: Session, fecha_inicio: datetime, fecha_fin: datetime, proveedor_id: int | None = None, gasto_id: int | None = None):
        """Detalle económico de facturas recibidas de proveedores."""
        InformesService._validar_periodo(fecha_inicio, fecha_fin)
        consulta = (
            db.query(FacturaProveedor)
            .options(joinedload(FacturaProveedor.proveedor))
            .filter(
                FacturaProveedor.fecha_factura >= fecha_inicio.date(),
                FacturaProveedor.fecha_factura < fecha_fin.date(),
            )
        )
        if proveedor_id:
            consulta = consulta.filter(FacturaProveedor.proveedor_id == proveedor_id)
        if gasto_id:
            consulta = consulta.filter(FacturaProveedor.id == gasto_id)
        facturas = consulta.order_by(FacturaProveedor.fecha_factura.asc(), FacturaProveedor.id.asc()).all()
        filas = []
        base_total = iva_total = total = Decimal("0.00")
        for factura in facturas:
            proveedor = factura.proveedor
            base = Decimal(factura.base_imponible or 0)
            iva = Decimal(factura.iva or 0)
            importe_total = Decimal(factura.total or 0)
            base_total += base
            iva_total += iva
            total += importe_total
            filas.append({
                "fecha": factura.fecha_factura,
                "numero": factura.numero_factura,
                "tipo_gasto": factura.tipo_gasto or "COMPRA",
                "tercero": getattr(proveedor, "nombre", None) or "-",
                "nif": getattr(proveedor, "cif", None) or "-",
                "base": base,
                "iva": iva,
                "total": importe_total,
                "estado": factura.estado_pago,
            })
        return {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "filas": filas,
            "totales": {"documentos": len(filas), "base": base_total, "iva": iva_total, "total": total},
        }
