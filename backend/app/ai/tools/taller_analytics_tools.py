from datetime import datetime

from sqlalchemy import (
    func,
    case
)

from sqlalchemy.orm import Session

from app.models.orden_reparacion import (
    OrdenReparacion,
    EstadoReparacion
)

from app.models.vehiculo import Vehiculo
from app.models.cliente import Cliente


# =========================================================
# TOOLS
# =========================================================

TALLER_ANALYTICS_TOOLS = [

    {
        "type": "function",
        "function": {

            "name": "resumen_actividad_taller",

            "description": (
                "Obtiene un resumen de la actividad del taller "
                "en un periodo: órdenes creadas, cerradas, "
                "facturadas, abiertas, en proceso e importes "
                "de las órdenes."
            ),

            "parameters": {
                "type": "object",

                "properties": {

                    "fecha_desde": {
                        "type": "string"
                    },

                    "fecha_hasta": {
                        "type": "string"
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


    {
        "type": "function",
        "function": {

            "name": "tiempo_medio_reparacion",

            "description": (
                "Calcula cuánto tiempo tardan de media las "
                "órdenes de reparación desde la entrada del "
                "vehículo hasta su salida. Solo utiliza órdenes "
                "normales con fecha de salida registrada."
            ),

            "parameters": {
                "type": "object",

                "properties": {

                    "fecha_desde": {
                        "type": "string"
                    },

                    "fecha_hasta": {
                        "type": "string"
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


    {
        "type": "function",
        "function": {

            "name": "vehiculos_mas_recurrentes",

            "description": (
                "Obtiene los vehículos que más órdenes de "
                "reparación han tenido en un periodo. Sirve "
                "para detectar vehículos recurrentes."
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
    },


    {
        "type": "function",
        "function": {

            "name": "ordenes_abiertas_antiguas",

            "description": (
                "Obtiene las órdenes normales que siguen abiertas "
                "o en proceso desde hace más tiempo. Úsala para "
                "detectar reparaciones atascadas o que requieren "
                "seguimiento."
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
    },


    {
        "type": "function",
        "function": {

            "name": "ranking_clientes_visitas_taller",

            "description": (
                "Obtiene los clientes cuyos vehículos han "
                "generado más órdenes de reparación durante "
                "un periodo."
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
            "Fecha no válida para Analytics del taller."
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


# =========================================================
# RESUMEN ACTIVIDAD
# =========================================================

def resumen_actividad_taller(
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
                OrdenReparacion.id
            ).label(
                "total_ordenes"
            ),

            func.sum(
                case(
                    (
                        OrdenReparacion.estado
                        == EstadoReparacion.ABIERTA.value,
                        1
                    ),
                    else_=0
                )
            ).label(
                "abiertas"
            ),

            func.sum(
                case(
                    (
                        OrdenReparacion.estado
                        == EstadoReparacion.EN_PROCESO.value,
                        1
                    ),
                    else_=0
                )
            ).label(
                "en_proceso"
            ),

            func.sum(
                case(
                    (
                        OrdenReparacion.estado
                        == EstadoReparacion.CERRADA.value,
                        1
                    ),
                    else_=0
                )
            ).label(
                "cerradas"
            ),

            func.sum(
                case(
                    (
                        OrdenReparacion.estado
                        == EstadoReparacion.FACTURADA.value,
                        1
                    ),
                    else_=0
                )
            ).label(
                "facturadas"
            ),

            func.coalesce(
                func.sum(
                    OrdenReparacion.importe_total
                ),
                0
            ).label(
                "importe_ordenes"
            ),

            func.coalesce(
                func.avg(
                    OrdenReparacion.importe_total
                ),
                0
            ).label(
                "importe_medio"
            )

        )

        .filter(

            OrdenReparacion.tipo == "OR",

            OrdenReparacion.fecha_entrada >= desde,

            OrdenReparacion.fecha_entrada < hasta

        )

        .one()
    )


    return {

        "periodo": {
            "desde": desde.isoformat(),
            "hasta": hasta.isoformat()
        },

        "ordenes_creadas":
            int(
                resultado.total_ordenes
                or 0
            ),

        "por_estado": {

            "abiertas":
                int(
                    resultado.abiertas
                    or 0
                ),

            "en_proceso":
                int(
                    resultado.en_proceso
                    or 0
                ),

            "cerradas":
                int(
                    resultado.cerradas
                    or 0
                ),

            "facturadas":
                int(
                    resultado.facturadas
                    or 0
                )
        },

        "importe_total_ordenes":
            _float(
                resultado.importe_ordenes
            ),

        "importe_medio_orden":
            _float(
                resultado.importe_medio
            )
    }


# =========================================================
# TIEMPO MEDIO DE REPARACIÓN
# =========================================================

def tiempo_medio_reparacion(
    db: Session,
    fecha_desde: str,
    fecha_hasta: str
) -> dict:

    desde, hasta = _validar_periodo(
        fecha_desde,
        fecha_hasta
    )


    ordenes = (

        db.query(
            OrdenReparacion.fecha_entrada,
            OrdenReparacion.fecha_salida
        )

        .filter(

            OrdenReparacion.tipo == "OR",

            OrdenReparacion.fecha_entrada >= desde,

            OrdenReparacion.fecha_entrada < hasta,

            OrdenReparacion.fecha_salida.isnot(None)

        )

        .all()
    )


    if not ordenes:

        return {

            "numero_reparaciones":
                0,

            "tiempo_medio_horas":
                0,

            "tiempo_medio_dias":
                0
        }


    horas = []


    for orden in ordenes:

        diferencia = (
            orden.fecha_salida
            -
            orden.fecha_entrada
        )

        horas.append(
            diferencia.total_seconds()
            / 3600
        )


    media_horas = (
        sum(horas)
        /
        len(horas)
    )


    return {

        "numero_reparaciones":
            len(horas),

        "tiempo_medio_horas":
            round(
                media_horas,
                2
            ),

        "tiempo_medio_dias":
            round(
                media_horas / 24,
                2
            )
    }


# =========================================================
# VEHÍCULOS RECURRENTES
# =========================================================

def vehiculos_mas_recurrentes(
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

            Vehiculo.id.label(
                "vehiculo_id"
            ),

            Vehiculo.matricula,

            Vehiculo.marca,

            Vehiculo.modelo,

            func.count(
                OrdenReparacion.id
            ).label(
                "numero_ordenes"
            )

        )

        .join(
            OrdenReparacion,
            OrdenReparacion.vehiculo_id
            == Vehiculo.id
        )

        .filter(

            OrdenReparacion.tipo == "OR",

            OrdenReparacion.fecha_entrada >= desde,

            OrdenReparacion.fecha_entrada < hasta

        )

        .group_by(
            Vehiculo.id,
            Vehiculo.matricula,
            Vehiculo.marca,
            Vehiculo.modelo
        )

        .order_by(
            func.count(
                OrdenReparacion.id
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
                posicion,

            "vehiculo_id":
                fila.vehiculo_id,

            "matricula":
                fila.matricula,

            "marca":
                fila.marca,

            "modelo":
                fila.modelo,

            "numero_ordenes":
                int(
                    fila.numero_ordenes
                    or 0
                )
        }

        for posicion, fila
        in enumerate(
            resultados,
            start=1
        )
    ]


# =========================================================
# ÓRDENES ABIERTAS MÁS ANTIGUAS
# =========================================================

def ordenes_abiertas_antiguas(
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


    ahora = datetime.utcnow()


    ordenes = (

        db.query(
            OrdenReparacion
        )

        .filter(

            OrdenReparacion.tipo == "OR",

            OrdenReparacion.estado.in_([
                EstadoReparacion.ABIERTA.value,
                EstadoReparacion.EN_PROCESO.value
            ])

        )

        .order_by(
            OrdenReparacion.fecha_entrada.asc()
        )

        .limit(
            limite
        )

        .all()
    )


    resultado = []


    for orden in ordenes:

        horas_abierta = (
            ahora
            -
            orden.fecha_entrada
        ).total_seconds() / 3600


        resultado.append({

            "id":
                orden.id,

            "numero":
                orden.numero,

            "estado":
                orden.estado,

            "vehiculo_id":
                orden.vehiculo_id,

            "descripcion_averia":
                orden.descripcion_averia,

            "fecha_entrada":
                orden.fecha_entrada.isoformat(),

            "horas_abierta":
                round(
                    horas_abierta,
                    2
                ),

            "dias_abierta":
                round(
                    horas_abierta / 24,
                    2
                )
        })


    return resultado


# =========================================================
# CLIENTES CON MÁS VISITAS
# =========================================================

def ranking_clientes_visitas_taller(
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
                OrdenReparacion.id
            ).label(
                "visitas"
            )

        )

        .join(
            Vehiculo,
            Vehiculo.cliente_id
            == Cliente.id
        )

        .join(
            OrdenReparacion,
            OrdenReparacion.vehiculo_id
            == Vehiculo.id
        )

        .filter(

            OrdenReparacion.tipo == "OR",

            OrdenReparacion.fecha_entrada >= desde,

            OrdenReparacion.fecha_entrada < hasta

        )

        .group_by(
            Cliente.id,
            Cliente.nombre
        )

        .order_by(
            func.count(
                OrdenReparacion.id
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
                posicion,

            "cliente_id":
                fila.cliente_id,

            "nombre":
                fila.nombre,

            "visitas":
                int(
                    fila.visitas
                    or 0
                )
        }

        for posicion, fila
        in enumerate(
            resultados,
            start=1
        )
    ]
"""Herramientas IA de carga operativa, recurrencia y actividad del taller."""
