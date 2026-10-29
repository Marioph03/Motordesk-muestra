from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.factura import (
    Factura,
    EstadoFactura
)

from app.models.pago_factura import PagoFactura
from app.models.cliente import Cliente


# =========================================================
# DEFINICIÓN DE TOOLS
# =========================================================

COBROS_TOOLS = [

    # =====================================================
    # COBROS DE UN PERIODO
    # =====================================================

    {
        "type": "function",
        "function": {

            "name": "resumen_cobros",

            "description": (
                "Calcula cuánto dinero se ha cobrado realmente "
                "en un periodo utilizando los pagos registrados "
                "en MotorDesk. Permite responder cuánto se ha "
                "cobrado hoy, esta semana, este mes o en cualquier "
                "intervalo."
            ),

            "parameters": {
                "type": "object",

                "properties": {

                    "fecha_desde": {
                        "type": "string",
                        "description": (
                            "Inicio del periodo en formato ISO 8601."
                        )
                    },

                    "fecha_hasta": {
                        "type": "string",
                        "description": (
                            "Final del periodo en formato ISO 8601. "
                            "El límite superior no se incluye."
                        )
                    }
                },

                "required": [
                    "fecha_desde",
                    "fecha_hasta"
                ],

                "additionalProperties": False
            }
        }
    },


    # =====================================================
    # DEUDA TOTAL
    # =====================================================

    {
        "type": "function",
        "function": {

            "name": "resumen_deuda_pendiente",

            "description": (
                "Calcula exactamente cuánto dinero queda pendiente "
                "de cobrar de las facturas reales emitidas. "
                "Resta a cada factura la suma de los pagos "
                "registrados y nunca considera deuda negativa."
            ),

            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },


    # =====================================================
    # SITUACIÓN DE UNA FACTURA
    # =====================================================

    {
        "type": "function",
        "function": {

            "name": "obtener_situacion_cobro_factura",

            "description": (
                "Obtiene el estado económico exacto de una factura: "
                "total, cantidad cobrada, cantidad pendiente e "
                "historial de pagos."
            ),

            "parameters": {
                "type": "object",

                "properties": {

                    "factura_id": {
                        "type": "integer",
                        "description": "ID interno de la factura."
                    }
                },

                "required": [
                    "factura_id"
                ],

                "additionalProperties": False
            }
        }
    },


    # =====================================================
    # DEUDA DE CLIENTE
    # =====================================================

    {
        "type": "function",
        "function": {

            "name": "obtener_deuda_cliente",

            "description": (
                "Calcula exactamente cuánto dinero debe un cliente "
                "sumando el importe pendiente de sus facturas reales "
                "emitidas. Utilízala después de identificar al cliente."
            ),

            "parameters": {
                "type": "object",

                "properties": {

                    "cliente_id": {
                        "type": "integer",
                        "description": "ID interno del cliente."
                    }
                },

                "required": [
                    "cliente_id"
                ],

                "additionalProperties": False
            }
        }
    },


    # =====================================================
    # CLIENTES CON DEUDA
    # =====================================================

    {
        "type": "function",
        "function": {

            "name": "ranking_clientes_deuda",

            "description": (
                "Obtiene los clientes con mayor cantidad pendiente "
                "de pago, calculada a partir de sus facturas reales "
                "emitidas y los pagos registrados."
            ),

            "parameters": {
                "type": "object",

                "properties": {

                    "limite": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50
                    }
                },

                "additionalProperties": False
            }
        }
    }

]


# =========================================================
# HELPERS
# =========================================================

def _float(valor) -> float:
    return float(valor or 0)


def _parsear_fecha(valor: str) -> datetime:

    try:
        return datetime.fromisoformat(
            valor.replace("Z", "+00:00")
        )

    except (ValueError, AttributeError) as error:
        raise ValueError(
            "Fecha no válida para Analytics de cobros."
        ) from error


def _validar_periodo(
    fecha_desde: str,
    fecha_hasta: str
):

    desde = _parsear_fecha(fecha_desde)
    hasta = _parsear_fecha(fecha_hasta)

    if hasta <= desde:
        raise ValueError(
            "El periodo indicado no es válido."
        )

    return desde, hasta


def _subquery_pagos(db: Session):
    """
    Devuelve por factura la suma total de pagos registrados.
    """

    return (
        db.query(
            PagoFactura.factura_id.label(
                "factura_id"
            ),

            func.coalesce(
                func.sum(PagoFactura.importe),
                0
            ).label(
                "total_pagado"
            )
        )

        .group_by(
            PagoFactura.factura_id
        )

        .subquery()
    )


# =========================================================
# RESUMEN DE COBROS
# =========================================================

def resumen_cobros(
    db: Session,
    fecha_desde: str,
    fecha_hasta: str
) -> dict:

    desde, hasta = _validar_periodo(
        fecha_desde,
        fecha_hasta
    )

    resultado = (
        db.query(

            func.count(
                PagoFactura.id
            ).label(
                "numero_pagos"
            ),

            func.coalesce(
                func.sum(
                    PagoFactura.importe
                ),
                0
            ).label(
                "total_cobrado"
            )

        )

        .join(
            Factura,
            PagoFactura.factura_id
            == Factura.id
        )

        .filter(

            PagoFactura.fecha_pago >= desde,
            PagoFactura.fecha_pago < hasta,

            Factura.estado
            == EstadoFactura.EMITIDA.value,

            Factura.es_prueba.is_(False)

        )

        .one()
    )


    # ---------------------------------------------
    # DESGLOSE POR MÉTODO
    # ---------------------------------------------

    metodos = (
        db.query(

            PagoFactura.metodo_pago,

            func.count(
                PagoFactura.id
            ).label(
                "numero_pagos"
            ),

            func.sum(
                PagoFactura.importe
            ).label(
                "total"
            )

        )

        .join(
            Factura,
            PagoFactura.factura_id
            == Factura.id
        )

        .filter(

            PagoFactura.fecha_pago >= desde,
            PagoFactura.fecha_pago < hasta,

            Factura.estado
            == EstadoFactura.EMITIDA.value,

            Factura.es_prueba.is_(False)

        )

        .group_by(
            PagoFactura.metodo_pago
        )

        .order_by(
            func.sum(
                PagoFactura.importe
            ).desc()
        )

        .all()
    )


    return {

        "periodo": {
            "desde": desde.isoformat(),
            "hasta": hasta.isoformat()
        },

        "numero_pagos":
            int(
                resultado.numero_pagos
                or 0
            ),

        "total_cobrado":
            _float(
                resultado.total_cobrado
            ),

        "por_metodo": [

            {
                "metodo":
                    fila.metodo_pago,

                "numero_pagos":
                    int(
                        fila.numero_pagos
                        or 0
                    ),

                "total":
                    _float(
                        fila.total
                    )
            }

            for fila in metodos
        ],

        "criterio": (
            "Pagos registrados de facturas "
            "EMITIDAS y no de prueba."
        )
    }


# =========================================================
# DEUDA TOTAL
# =========================================================

def resumen_deuda_pendiente(
    db: Session
) -> dict:

    pagos = _subquery_pagos(db)


    facturas = (
        db.query(

            Factura.id,
            Factura.total,

            func.coalesce(
                pagos.c.total_pagado,
                0
            ).label(
                "pagado"
            )

        )

        .outerjoin(
            pagos,
            pagos.c.factura_id
            == Factura.id
        )

        .filter(

            Factura.estado
            == EstadoFactura.EMITIDA.value,

            Factura.es_prueba.is_(False)

        )

        .all()
    )


    deuda_total = 0.0
    facturas_con_deuda = 0
    facturas_pagadas = 0


    for factura in facturas:

        total = _float(
            factura.total
        )

        pagado = _float(
            factura.pagado
        )

        pendiente = max(
            0,
            total - pagado
        )


        if pendiente > 0:

            deuda_total += pendiente
            facturas_con_deuda += 1

        else:

            facturas_pagadas += 1


    return {

        "deuda_total":
            round(
                deuda_total,
                2
            ),

        "facturas_con_deuda":
            facturas_con_deuda,

        "facturas_saldadas":
            facturas_pagadas,

        "facturas_analizadas":
            len(facturas),

        "criterio": (
            "Factura.total menos suma de "
            "pagos registrados. Nunca se "
            "considera deuda negativa."
        )
    }


# =========================================================
# SITUACIÓN DE UNA FACTURA
# =========================================================

def obtener_situacion_cobro_factura(
    db: Session,
    factura_id: int
) -> dict:

    if not factura_id:

        return {
            "encontrada": False
        }


    factura = (
        db.query(Factura)

        .filter(
            Factura.id
            == factura_id
        )

        .first()
    )


    if not factura:

        return {
            "encontrada": False
        }


    pagos = (
        db.query(PagoFactura)

        .filter(
            PagoFactura.factura_id
            == factura_id
        )

        .order_by(
            PagoFactura.fecha_pago.asc()
        )

        .all()
    )


    total_pagado = sum(
        _float(pago.importe)
        for pago in pagos
    )


    total_factura = _float(
        factura.total
    )


    pendiente = max(
        0,
        total_factura
        - total_pagado
    )


    return {

        "encontrada": True,

        "factura_id":
            factura.id,

        "numero":
            factura.numero,

        "estado":
            factura.estado,

        "estado_cobro":
            factura.estado_cobro,

        "es_prueba":
            bool(
                factura.es_prueba
            ),

        "total_factura":
            total_factura,

        "total_pagado":
            round(
                total_pagado,
                2
            ),

        "pendiente":
            round(
                pendiente,
                2
            ),

        "saldada":
            pendiente <= 0,

        "numero_pagos":
            len(pagos),

        "pagos": [

            {
                "id":
                    pago.id,

                "importe":
                    _float(
                        pago.importe
                    ),

                "metodo_pago":
                    pago.metodo_pago,

                "referencia":
                    pago.referencia,

                "fecha_pago": (
                    pago.fecha_pago.isoformat()
                    if pago.fecha_pago
                    else None
                ),

                "observaciones":
                    pago.observaciones
            }

            for pago in pagos
        ]
    }


# =========================================================
# DEUDA CLIENTE
# =========================================================

def obtener_deuda_cliente(
    db: Session,
    cliente_id: int
) -> dict:

    if not cliente_id:

        return {
            "encontrado": False
        }


    cliente = (
        db.query(Cliente)

        .filter(
            Cliente.id
            == cliente_id
        )

        .first()
    )


    if not cliente:

        return {
            "encontrado": False
        }


    pagos = _subquery_pagos(db)


    facturas = (
        db.query(

            Factura.id,
            Factura.numero,
            Factura.total,
            Factura.fecha_emision,

            func.coalesce(
                pagos.c.total_pagado,
                0
            ).label(
                "pagado"
            )

        )

        .outerjoin(
            pagos,
            pagos.c.factura_id
            == Factura.id
        )

        .filter(

            Factura.cliente_id
            == cliente_id,

            Factura.estado
            == EstadoFactura.EMITIDA.value,

            Factura.es_prueba.is_(False)

        )

        .order_by(
            Factura.fecha_emision.desc()
        )

        .all()
    )


    deuda_total = 0.0
    pendientes = []


    for factura in facturas:

        total = _float(
            factura.total
        )

        pagado = _float(
            factura.pagado
        )

        pendiente = max(
            0,
            total - pagado
        )


        if pendiente <= 0:
            continue


        deuda_total += pendiente


        pendientes.append({

            "factura_id":
                factura.id,

            "numero":
                factura.numero,

            "fecha_emision": (
                factura.fecha_emision.isoformat()
                if factura.fecha_emision
                else None
            ),

            "total":
                total,

            "pagado":
                pagado,

            "pendiente":
                round(
                    pendiente,
                    2
                )
        })


    return {

        "encontrado": True,

        "cliente": {
            "id":
                cliente.id,

            "nombre":
                cliente.nombre
        },

        "deuda_total":
            round(
                deuda_total,
                2
            ),

        "numero_facturas_pendientes":
            len(pendientes),

        "facturas_pendientes":
            pendientes
    }


# =========================================================
# RANKING CLIENTES CON DEUDA
# =========================================================

def ranking_clientes_deuda(
    db: Session,
    limite: int = 10
) -> list[dict]:

    limite = max(
        1,
        min(
            limite or 10,
            50
        )
    )


    pagos = _subquery_pagos(db)


    facturas = (
        db.query(

            Factura.cliente_id,

            Factura.total,

            func.coalesce(
                pagos.c.total_pagado,
                0
            ).label(
                "pagado"
            )

        )

        .outerjoin(
            pagos,
            pagos.c.factura_id
            == Factura.id
        )

        .filter(

            Factura.estado
            == EstadoFactura.EMITIDA.value,

            Factura.es_prueba.is_(False)

        )

        .all()
    )


    deuda_por_cliente = {}


    for factura in facturas:

        total = _float(
            factura.total
        )

        pagado = _float(
            factura.pagado
        )

        pendiente = max(
            0,
            total - pagado
        )


        if pendiente <= 0:
            continue


        deuda_por_cliente[
            factura.cliente_id
        ] = (
            deuda_por_cliente.get(
                factura.cliente_id,
                0
            )
            +
            pendiente
        )


    if not deuda_por_cliente:
        return []


    clientes = (
        db.query(Cliente)

        .filter(
            Cliente.id.in_(
                deuda_por_cliente.keys()
            )
        )

        .all()
    )


    mapa_clientes = {
        cliente.id: cliente
        for cliente in clientes
    }


    ranking = sorted(
        deuda_por_cliente.items(),
        key=lambda item: item[1],
        reverse=True
    )[:limite]


    resultado = []


    for posicion, (
        cliente_id,
        deuda
    ) in enumerate(
        ranking,
        start=1
    ):

        cliente = mapa_clientes.get(
            cliente_id
        )


        resultado.append({

            "posicion":
                posicion,

            "cliente_id":
                cliente_id,

            "nombre": (
                cliente.nombre
                if cliente
                else None
            ),

            "deuda":
                round(
                    deuda,
                    2
                )
        })


    return resultado
"""Herramientas IA para cobros y deuda calculada desde pagos registrados."""
