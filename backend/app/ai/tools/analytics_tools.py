from datetime import datetime

from sqlalchemy import (
    func,
    case
)

from sqlalchemy.orm import Session

from app.models.factura import (
    Factura,
    EstadoFactura,
    EstadoCobro
)

from app.models.cliente import Cliente


# =========================================================
# DEFINICIÓN DE TOOLS
# =========================================================

ANALYTICS_TOOLS = [

    # =====================================================
    # RESUMEN FACTURACIÓN
    # =====================================================

    {
        "type": "function",
        "function": {

            "name": "resumen_facturacion",

            "description": (
                "Calcula la facturación real de MotorDesk "
                "dentro de un intervalo de fechas. "
                "Solo tiene en cuenta facturas EMITIDAS y "
                "excluye facturas de prueba. Úsala para "
                "preguntas como cuánto se ha facturado hoy, "
                "esta semana, este mes o en un periodo."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "fecha_desde": {
                        "type": "string",
                        "description": (
                            "Inicio del periodo en formato "
                            "ISO 8601."
                        )
                    },

                    "fecha_hasta": {
                        "type": "string",
                        "description": (
                            "Final del periodo en formato "
                            "ISO 8601. El límite superior "
                            "no se incluye."
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
    # COMPARAR FACTURACIÓN
    # =====================================================

    {
        "type": "function",
        "function": {

            "name": "comparar_facturacion",

            "description": (
                "Compara la facturación real entre dos "
                "periodos. Calcula total, diferencia "
                "absoluta y variación porcentual."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "periodo_1_desde": {
                        "type": "string"
                    },

                    "periodo_1_hasta": {
                        "type": "string"
                    },

                    "periodo_2_desde": {
                        "type": "string"
                    },

                    "periodo_2_hasta": {
                        "type": "string"
                    }

                },

                "required": [
                    "periodo_1_desde",
                    "periodo_1_hasta",
                    "periodo_2_desde",
                    "periodo_2_hasta"
                ],

                "additionalProperties": False
            }
        }
    },


    # =====================================================
    # PENDIENTE DE COBRO
    # =====================================================

    {
        "type": "function",
        "function": {

            "name": "resumen_pendiente_cobro",

            "description": (
                "Calcula el importe de facturas reales "
                "emitidas que todavía no constan como "
                "completamente pagadas. Distingue entre "
                "PENDIENTE y PARCIAL."
            ),

            "parameters": {

                "type": "object",

                "properties": {},

                "additionalProperties": False
            }
        }
    },


    # =====================================================
    # RANKING CLIENTES
    # =====================================================

    {
        "type": "function",
        "function": {

            "name":
                "ranking_clientes_facturacion",

            "description": (
                "Obtiene los clientes que más facturación "
                "real han generado dentro de un periodo. "
                "Solo cuenta facturas EMITIDAS y excluye "
                "facturas de prueba."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "fecha_desde": {
                        "type": "string"
                    },

                    "fecha_hasta": {
                        "type": "string"
                    },

                    "limite": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50
                    }

                },

                "required": [
                    "fecha_desde",
                    "fecha_hasta"
                ],

                "additionalProperties": False
            }
        }
    }

]


# =========================================================
# HELPERS
# =========================================================

def _float(valor) -> float:

    return float(
        valor or 0
    )


def _parsear_fecha(
    valor: str
) -> datetime:

    try:

        return datetime.fromisoformat(
            valor.replace(
                "Z",
                "+00:00"
            )
        )

    except (
        ValueError,
        AttributeError
    ) as error:

        raise ValueError(
            "Fecha no válida para Analytics."
        ) from error


def _validar_periodo(
    fecha_desde: str,
    fecha_hasta: str
):

    desde = _parsear_fecha(
        fecha_desde
    )

    hasta = _parsear_fecha(
        fecha_hasta
    )


    if hasta <= desde:

        raise ValueError(
            "El periodo indicado no es válido."
        )


    return desde, hasta


def _filtros_facturacion_real(
    desde: datetime,
    hasta: datetime
):

    return (

        Factura.estado
        == EstadoFactura.EMITIDA.value,

        Factura.es_prueba.is_(False),

        Factura.fecha_emision >= desde,

        Factura.fecha_emision < hasta

    )


def _calcular_periodo(
    db: Session,
    desde: datetime,
    hasta: datetime
) -> dict:

    resultado = (

        db.query(

            func.count(
                Factura.id
            ).label(
                "numero_facturas"
            ),

            func.coalesce(
                func.sum(
                    Factura.total
                ),
                0
            ).label(
                "total"
            ),

            func.coalesce(
                func.avg(
                    Factura.total
                ),
                0
            ).label(
                "ticket_medio"
            ),

            func.coalesce(
                func.sum(
                    Factura.base_imponible
                ),
                0
            ).label(
                "base_imponible"
            ),

            func.coalesce(
                func.sum(
                    Factura.cuota_iva
                ),
                0
            ).label(
                "iva"
            )

        )

        .filter(
            *_filtros_facturacion_real(
                desde,
                hasta
            )
        )

        .one()

    )


    return {

        "numero_facturas":
            int(
                resultado.numero_facturas
                or 0
            ),

        "base_imponible":
            _float(
                resultado.base_imponible
            ),

        "iva":
            _float(
                resultado.iva
            ),

        "total":
            _float(
                resultado.total
            ),

        "ticket_medio":
            _float(
                resultado.ticket_medio
            )

    }


# =========================================================
# RESUMEN FACTURACIÓN
# =========================================================

def resumen_facturacion(
    db: Session,
    fecha_desde: str,
    fecha_hasta: str
) -> dict:

    desde, hasta = _validar_periodo(
        fecha_desde,
        fecha_hasta
    )


    resultado = _calcular_periodo(
        db,
        desde,
        hasta
    )


    return {

        "periodo": {
            "desde":
                desde.isoformat(),

            "hasta":
                hasta.isoformat()
        },

        **resultado,

        "criterio": (
            "Solo facturas EMITIDAS "
            "y no marcadas como prueba."
        )

    }


# =========================================================
# COMPARAR FACTURACIÓN
# =========================================================

def comparar_facturacion(
    db: Session,
    periodo_1_desde: str,
    periodo_1_hasta: str,
    periodo_2_desde: str,
    periodo_2_hasta: str
) -> dict:

    desde_1, hasta_1 = _validar_periodo(
        periodo_1_desde,
        periodo_1_hasta
    )

    desde_2, hasta_2 = _validar_periodo(
        periodo_2_desde,
        periodo_2_hasta
    )


    p1 = _calcular_periodo(
        db,
        desde_1,
        hasta_1
    )

    p2 = _calcular_periodo(
        db,
        desde_2,
        hasta_2
    )


    diferencia = (
        p1["total"]
        -
        p2["total"]
    )


    if p2["total"] != 0:

        variacion = (
            diferencia
            /
            p2["total"]
        ) * 100

    elif p1["total"] > 0:

        variacion = None

    else:

        variacion = 0.0


    return {

        "periodo_1": {
            "desde":
                desde_1.isoformat(),

            "hasta":
                hasta_1.isoformat(),

            **p1
        },

        "periodo_2": {
            "desde":
                desde_2.isoformat(),

            "hasta":
                hasta_2.isoformat(),

            **p2
        },

        "diferencia":
            round(
                diferencia,
                2
            ),

        "variacion_porcentual": (
            round(
                variacion,
                2
            )

            if variacion is not None
            else None
        ),

        "criterio": (
            "Periodo 1 comparado "
            "contra periodo 2."
        )

    }


# =========================================================
# PENDIENTE DE COBRO
# =========================================================

def resumen_pendiente_cobro(
    db: Session
) -> dict:

    resultado = (

        db.query(

            func.count(
                Factura.id
            ).label(
                "numero_facturas"
            ),

            func.coalesce(

                func.sum(

                    case(

                        (
                            Factura.estado_cobro
                            == EstadoCobro.PENDIENTE.value,

                            Factura.total
                        ),

                        else_=0
                    )

                ),

                0

            ).label(
                "total_pendiente"
            ),

            func.coalesce(

                func.sum(

                    case(

                        (
                            Factura.estado_cobro
                            == EstadoCobro.PARCIAL.value,

                            Factura.total
                        ),

                        else_=0
                    )

                ),

                0

            ).label(
                "total_facturas_parciales"
            )

        )

        .filter(

            Factura.estado
            == EstadoFactura.EMITIDA.value,

            Factura.es_prueba.is_(False),

            Factura.estado_cobro.in_([
                EstadoCobro.PENDIENTE.value,
                EstadoCobro.PARCIAL.value
            ])

        )

        .one()

    )


    return {

        "numero_facturas_no_pagadas":
            int(
                resultado.numero_facturas
                or 0
            ),

        "importe_facturas_pendientes":
            _float(
                resultado.total_pendiente
            ),

        "importe_total_facturas_parciales":
            _float(
                resultado.total_facturas_parciales
            ),

        "advertencia": (
            "En facturas PARCIALES este valor "
            "representa el total de la factura, "
            "no necesariamente el importe exacto "
            "que queda por cobrar."
        )

    }


# =========================================================
# RANKING CLIENTES
# =========================================================

def ranking_clientes_facturacion(
    db: Session,
    fecha_desde: str,
    fecha_hasta: str,
    limite: int = 10
) -> list[dict]:

    desde, hasta = _validar_periodo(
        fecha_desde,
        fecha_hasta
    )


    limite = max(
        1,
        min(
            limite or 10,
            50
        )
    )


    resultados = (

        db.query(

            Cliente.id.label(
                "cliente_id"
            ),

            Cliente.nombre.label(
                "nombre"
            ),

            func.count(
                Factura.id
            ).label(
                "numero_facturas"
            ),

            func.sum(
                Factura.total
            ).label(
                "facturacion"
            )

        )

        .join(
            Factura,
            Factura.cliente_id
            == Cliente.id
        )

        .filter(
            *_filtros_facturacion_real(
                desde,
                hasta
            )
        )

        .group_by(
            Cliente.id,
            Cliente.nombre
        )

        .order_by(
            func.sum(
                Factura.total
            ).desc()
        )

        .limit(
            limite
        )

        .all()

    )


    return [

        {
            "posicion":
                indice,

            "cliente_id":
                fila.cliente_id,

            "nombre":
                fila.nombre,

            "numero_facturas":
                int(
                    fila.numero_facturas
                    or 0
                ),

            "facturacion":
                _float(
                    fila.facturacion
                )

        }

        for indice, fila
        in enumerate(
            resultados,
            start=1
        )

    ]
"""Herramientas IA de métricas financieras basadas en consultas controladas."""
