from datetime import datetime

from sqlalchemy.orm import Session

from app.ai.tools.analytics_tools import (
    resumen_facturacion,
    comparar_facturacion
)

from app.ai.tools.cobros_tools import (
    resumen_cobros,
    resumen_deuda_pendiente
)

from app.ai.tools.taller_analytics_tools import (
    resumen_actividad_taller,
    ordenes_abiertas_antiguas
)

from app.ai.tools.stock_analytics_tools import (
    resumen_valor_stock,
    resumen_reposicion_stock,
    resumen_compras_stock
)


# =========================================================
# TOOLS
# =========================================================

INSIGHTS_TOOLS = [

    {
        "type": "function",
        "function": {

            "name": "resumen_ejecutivo",

            "description": (
                "Genera una visión global del negocio del taller "
                "para un periodo y lo compara con otro periodo. "
                "Combina facturación, cobros, deuda, actividad "
                "del taller, órdenes pendientes, stock, "
                "reposición y compras. Debe utilizarse para "
                "preguntas generales como cómo va el taller, "
                "resumen del negocio, situación actual o qué "
                "aspectos requieren atención."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "fecha_desde": {
                        "type": "string",
                        "description": (
                            "Inicio del periodo actual "
                            "en formato ISO 8601."
                        )
                    },

                    "fecha_hasta": {
                        "type": "string",
                        "description": (
                            "Final exclusivo del periodo actual "
                            "en formato ISO 8601."
                        )
                    },

                    "comparacion_desde": {
                        "type": "string",
                        "description": (
                            "Inicio del periodo utilizado "
                            "como comparación."
                        )
                    },

                    "comparacion_hasta": {
                        "type": "string",
                        "description": (
                            "Final exclusivo del periodo "
                            "utilizado como comparación."
                        )
                    }
                },

                "required": [
                    "fecha_desde",
                    "fecha_hasta",
                    "comparacion_desde",
                    "comparacion_hasta"
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
    return float(valor or 0)


def _parsear_fecha(valor: str) -> datetime:

    try:
        return datetime.fromisoformat(
            valor.replace(
                "Z",
                "+00:00"
            )
        )

    except (ValueError, AttributeError) as error:

        raise ValueError(
            "Fecha no válida para MotorDesk Insights."
        ) from error


def _validar_periodo(
    desde: str,
    hasta: str
):

    fecha_desde = _parsear_fecha(
        desde
    )

    fecha_hasta = _parsear_fecha(
        hasta
    )

    if fecha_hasta <= fecha_desde:

        raise ValueError(
            "El periodo indicado no es válido."
        )

    return fecha_desde, fecha_hasta


# =========================================================
# GENERACIÓN DE ALERTAS
# =========================================================

def _generar_alertas(
    facturacion: dict,
    comparacion: dict,
    deuda: dict,
    taller: dict,
    ordenes_antiguas: list,
    stock: dict,
    reposicion: dict
) -> list[dict]:

    alertas = []


    # -----------------------------------------------------
    # FACTURACIÓN
    # -----------------------------------------------------

    variacion = comparacion.get(
        "variacion_porcentual"
    )


    if variacion is not None:

        if variacion <= -20:

            alertas.append({

                "nivel": "ALTA",

                "categoria": "FACTURACION",

                "mensaje": (
                    "La facturación ha descendido "
                    f"{abs(round(variacion, 2))}% "
                    "respecto al periodo comparado."
                )
            })

        elif variacion <= -10:

            alertas.append({

                "nivel": "MEDIA",

                "categoria": "FACTURACION",

                "mensaje": (
                    "La facturación ha descendido "
                    f"{abs(round(variacion, 2))}% "
                    "respecto al periodo comparado."
                )
            })


    # -----------------------------------------------------
    # DEUDA
    # -----------------------------------------------------

    deuda_total = _float(
        deuda.get(
            "deuda_total"
        )
    )

    facturacion_total = _float(
        facturacion.get(
            "total"
        )
    )


    if (
        deuda_total > 0
        and
        facturacion_total > 0
    ):

        ratio_deuda = (
            deuda_total
            /
            facturacion_total
        ) * 100


        if ratio_deuda >= 50:

            alertas.append({

                "nivel": "ALTA",

                "categoria": "COBROS",

                "mensaje": (
                    "La deuda pendiente acumulada "
                    "es elevada en relación con la "
                    "facturación del periodo."
                ),

                "ratio_referencia":
                    round(
                        ratio_deuda,
                        2
                    )
            })

        elif ratio_deuda >= 25:

            alertas.append({

                "nivel": "MEDIA",

                "categoria": "COBROS",

                "mensaje": (
                    "Existe una cantidad relevante "
                    "pendiente de cobro."
                ),

                "ratio_referencia":
                    round(
                        ratio_deuda,
                        2
                    )
            })


    # -----------------------------------------------------
    # ÓRDENES ANTIGUAS
    # -----------------------------------------------------

    if ordenes_antiguas:

        ordenes_mas_7_dias = [

            orden

            for orden in ordenes_antiguas

            if _float(
                orden.get(
                    "dias_abierta"
                )
            ) >= 7
        ]


        if ordenes_mas_7_dias:

            alertas.append({

                "nivel": (
                    "ALTA"
                    if len(
                        ordenes_mas_7_dias
                    ) >= 5
                    else "MEDIA"
                ),

                "categoria": "TALLER",

                "mensaje": (
                    f"Hay {len(ordenes_mas_7_dias)} "
                    "órdenes abiertas o en proceso "
                    "desde hace al menos 7 días."
                )
            })


    # -----------------------------------------------------
    # STOCK
    # -----------------------------------------------------

    agotados = int(
        stock.get(
            "articulos_agotados",
            0
        )
        or 0
    )

    bajo_minimos = int(
        stock.get(
            "articulos_bajo_minimos",
            0
        )
        or 0
    )


    if agotados > 0:

        alertas.append({

            "nivel": "ALTA",

            "categoria": "STOCK",

            "mensaje": (
                f"Hay {agotados} artículos "
                "activos sin existencias."
            )
        })


    if bajo_minimos > agotados:

        alertas.append({

            "nivel": "MEDIA",

            "categoria": "STOCK",

            "mensaje": (
                f"Hay {bajo_minimos} artículos "
                "en stock mínimo o por debajo."
            )
        })


    # -----------------------------------------------------
    # REPOSICIÓN
    # -----------------------------------------------------

    articulos_reponer = int(
        reposicion.get(
            "articulos_a_reponer",
            0
        )
        or 0
    )


    if articulos_reponer > 0:

        alertas.append({

            "nivel": "INFO",

            "categoria": "REPOSICION",

            "mensaje": (
                f"{articulos_reponer} artículos "
                "podrían necesitar reposición."
            ),

            "coste_estimado":
                _float(
                    reposicion.get(
                        "coste_estimado_reposicion"
                    )
                )
        })


    # -----------------------------------------------------
    # SIN ALERTAS
    # -----------------------------------------------------

    if not alertas:

        alertas.append({

            "nivel": "INFO",

            "categoria": "GENERAL",

            "mensaje": (
                "No se han detectado alertas "
                "destacables con las reglas actuales."
            )
        })


    prioridad = {
        "ALTA": 0,
        "MEDIA": 1,
        "INFO": 2
    }


    alertas.sort(
        key=lambda alerta:
            prioridad.get(
                alerta["nivel"],
                99
            )
    )


    return alertas


# =========================================================
# RESUMEN EJECUTIVO
# =========================================================

def resumen_ejecutivo(
    db: Session,
    fecha_desde: str,
    fecha_hasta: str,
    comparacion_desde: str,
    comparacion_hasta: str
) -> dict:

    # Validamos antes de lanzar todas las consultas.

    desde, hasta = _validar_periodo(
        fecha_desde,
        fecha_hasta
    )

    comp_desde, comp_hasta = _validar_periodo(
        comparacion_desde,
        comparacion_hasta
    )


    # =====================================================
    # FACTURACIÓN
    # =====================================================

    facturacion = resumen_facturacion(
        db=db,
        fecha_desde=desde.isoformat(),
        fecha_hasta=hasta.isoformat()
    )


    comparacion = comparar_facturacion(
        db=db,

        periodo_1_desde=desde.isoformat(),
        periodo_1_hasta=hasta.isoformat(),

        periodo_2_desde=comp_desde.isoformat(),
        periodo_2_hasta=comp_hasta.isoformat()
    )


    # =====================================================
    # COBROS
    # =====================================================

    cobros = resumen_cobros(
        db=db,
        fecha_desde=desde.isoformat(),
        fecha_hasta=hasta.isoformat()
    )


    deuda = resumen_deuda_pendiente(
        db=db
    )


    # =====================================================
    # TALLER
    # =====================================================

    taller = resumen_actividad_taller(
        db=db,
        fecha_desde=desde.isoformat(),
        fecha_hasta=hasta.isoformat()
    )


    ordenes_antiguas = (
        ordenes_abiertas_antiguas(
            db=db,
            limite=10
        )
    )


    # =====================================================
    # STOCK
    # =====================================================

    stock = resumen_valor_stock(
        db=db
    )


    reposicion = resumen_reposicion_stock(
        db=db,
        limite=50
    )


    # =====================================================
    # COMPRAS
    # =====================================================

    compras = resumen_compras_stock(
        db=db,
        fecha_desde=desde.isoformat(),
        fecha_hasta=hasta.isoformat()
    )


    # =====================================================
    # ALERTAS
    # =====================================================

    alertas = _generar_alertas(

        facturacion=facturacion,

        comparacion=comparacion,

        deuda=deuda,

        taller=taller,

        ordenes_antiguas=ordenes_antiguas,

        stock=stock,

        reposicion=reposicion
    )


    # =====================================================
    # KPI
    # =====================================================

    facturado = _float(
        facturacion.get(
            "total"
        )
    )

    cobrado = _float(
        cobros.get(
            "total_cobrado"
        )
    )


    ratio_cobro_periodo = (

        round(
            (
                cobrado
                /
                facturado
            ) * 100,
            2
        )

        if facturado > 0

        else None
    )


    # =====================================================
    # RESPUESTA
    # =====================================================

    return {

        "periodo_actual": {
            "desde":
                desde.isoformat(),

            "hasta":
                hasta.isoformat()
        },

        "periodo_comparado": {
            "desde":
                comp_desde.isoformat(),

            "hasta":
                comp_hasta.isoformat()
        },


        # ---------------------------------------------
        # KPI PRINCIPALES
        # ---------------------------------------------

        "kpi": {

            "facturacion":
                facturado,

            "variacion_facturacion_porcentual":
                comparacion.get(
                    "variacion_porcentual"
                ),

            "cobrado_en_periodo":
                cobrado,

            "ratio_cobro_sobre_facturacion":
                ratio_cobro_periodo,

            "deuda_pendiente_total":
                _float(
                    deuda.get(
                        "deuda_total"
                    )
                ),

            "ordenes_creadas":
                taller.get(
                    "ordenes_creadas",
                    0
                ),

            "valor_stock_a_coste":
                _float(
                    stock.get(
                        "valor_stock_a_coste"
                    )
                ),

            "compras_recibidas_sin_iva":
                _float(
                    compras.get(
                        "coste_mercancia_recibida_sin_iva"
                    )
                )
        },


        # ---------------------------------------------
        # BLOQUES COMPLETOS
        # ---------------------------------------------

        "facturacion":
            facturacion,

        "comparacion_facturacion":
            comparacion,

        "cobros":
            cobros,

        "deuda":
            deuda,

        "taller":
            taller,

        "ordenes_que_requieren_revision":
            ordenes_antiguas,

        "stock":
            stock,

        "reposicion":
            reposicion,

        "compras":
            compras,


        # ---------------------------------------------
        # INSIGHTS DETERMINISTAS
        # ---------------------------------------------

        "alertas":
            alertas
    }
"""Herramientas IA de resumen ejecutivo y alertas basadas en reglas reales."""
