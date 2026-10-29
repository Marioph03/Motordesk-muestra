from datetime import datetime

from sqlalchemy import (
    func,
    desc,
    case
)

from sqlalchemy.orm import Session

from app.models.articulo_stock import ArticuloStock

from app.models.movimiento_stock import (
    MovimientoStock,
    TipoMovimientoStock
)

from app.models.linea_pedido_compra import (
    LineaPedidoCompra
)

from app.models.pedido_compra import PedidoCompra


# =========================================================
# DEFINICIÓN DE TOOLS
# =========================================================

STOCK_ANALYTICS_TOOLS = [

    # =====================================================
    # VALOR DEL ALMACÉN
    # =====================================================

    {
        "type": "function",
        "function": {

            "name": "resumen_valor_stock",

            "description": (
                "Calcula el valor económico actual del almacén "
                "de MotorDesk utilizando stock_actual por coste. "
                "También devuelve número de artículos, unidades "
                "almacenadas, artículos agotados y bajo mínimos."
            ),

            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },


    # =====================================================
    # ARTÍCULOS MÁS CONSUMIDOS
    # =====================================================

    {
        "type": "function",
        "function": {

            "name": "articulos_mas_consumidos",

            "description": (
                "Obtiene los artículos más consumidos por órdenes "
                "de reparación dentro de un periodo. Utiliza "
                "movimientos CONSUMO_ORDEN y descuenta las "
                "DEVOLUCION_ORDEN para calcular consumo neto."
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


    # =====================================================
    # REPOSICIÓN
    # =====================================================

    {
        "type": "function",
        "function": {

            "name": "resumen_reposicion_stock",

            "description": (
                "Analiza los artículos activos cuyo stock actual "
                "es igual o inferior al stock mínimo. Calcula las "
                "unidades necesarias para recuperar al menos el "
                "stock mínimo y su coste estimado."
            ),

            "parameters": {
                "type": "object",

                "properties": {

                    "limite": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100
                    }
                },

                "additionalProperties": False
            }
        }
    },


    # =====================================================
    # RESUMEN COMPRAS
    # =====================================================

    {
        "type": "function",
        "function": {

            "name": "resumen_compras_stock",

            "description": (
                "Analiza las compras de artículos realizadas "
                "en un periodo utilizando las líneas de pedidos "
                "de compra. Devuelve cantidades pedidas, recibidas "
                "y valor económico. Úsala para analizar compras "
                "a proveedores, no consumo del almacén."
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


    # =====================================================
    # ARTÍCULOS MÁS COMPRADOS
    # =====================================================

    {
        "type": "function",
        "function": {

            "name": "articulos_mas_comprados",

            "description": (
                "Obtiene los artículos con mayor cantidad "
                "recibida mediante pedidos de compra durante "
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
    },


    # =====================================================
    # HISTÓRICO DE COSTES
    # =====================================================

    {
        "type": "function",
        "function": {

            "name": "analizar_coste_articulo",

            "description": (
                "Analiza el histórico del coste de compra de un "
                "artículo utilizando los costes unitarios guardados "
                "en las líneas de pedidos de compra. Permite saber "
                "si un recambio se está comprando más caro o barato "
                "que anteriormente."
            ),

            "parameters": {
                "type": "object",

                "properties": {

                    "articulo_id": {
                        "type": "integer"
                    },

                    "limite": {
                        "type": "integer",
                        "minimum": 2,
                        "maximum": 50
                    }
                },

                "required": [
                    "articulo_id"
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
            "Fecha no válida para Analytics de stock."
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
# VALOR DEL STOCK
# =========================================================

def resumen_valor_stock(
    db: Session
) -> dict:

    articulos = (

        db.query(
            ArticuloStock
        )

        .filter(
            ArticuloStock.activo.is_(True)
        )

        .all()
    )


    valor_coste = 0.0
    valor_venta = 0.0
    unidades = 0.0

    agotados = 0
    bajo_minimos = 0


    for articulo in articulos:

        stock = max(
            0,
            _float(
                articulo.stock_actual
            )
        )

        coste = _float(
            articulo.coste
        )

        precio_venta = _float(
            articulo.precio_venta
        )

        minimo = _float(
            articulo.stock_minimo
        )


        unidades += stock

        valor_coste += (
            stock * coste
        )

        valor_venta += (
            stock * precio_venta
        )


        if stock <= 0:
            agotados += 1

        if stock <= minimo:
            bajo_minimos += 1


    return {

        "articulos_activos":
            len(articulos),

        "unidades_en_stock":
            round(
                unidades,
                2
            ),

        "valor_stock_a_coste":
            round(
                valor_coste,
                2
            ),

        "valor_stock_a_precio_venta":
            round(
                valor_venta,
                2
            ),

        "margen_bruto_potencial":
            round(
                valor_venta
                - valor_coste,
                2
            ),

        "articulos_agotados":
            agotados,

        "articulos_bajo_minimos":
            bajo_minimos,

        "criterio": (
            "Valor actual calculado como "
            "stock_actual multiplicado por coste."
        )
    }


# =========================================================
# ARTÍCULOS MÁS CONSUMIDOS
# =========================================================

def articulos_mas_consumidos(
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


    movimientos = (

        db.query(

            MovimientoStock.articulo_id,

            func.sum(

                case(
                    (
                        MovimientoStock.tipo
                        ==
                        TipoMovimientoStock
                        .CONSUMO_ORDEN
                        .value,

                        MovimientoStock.cantidad
                    ),

                    else_=0
                )

            ).label(
                "consumido"
            ),

            func.sum(

                case(
                    (
                        MovimientoStock.tipo
                        ==
                        TipoMovimientoStock
                        .DEVOLUCION_ORDEN
                        .value,

                        MovimientoStock.cantidad
                    ),

                    else_=0
                )

            ).label(
                "devuelto"
            )

        )

        .filter(

            MovimientoStock.fecha >= desde,

            MovimientoStock.fecha < hasta,

            MovimientoStock.tipo.in_([
                TipoMovimientoStock
                .CONSUMO_ORDEN
                .value,

                TipoMovimientoStock
                .DEVOLUCION_ORDEN
                .value
            ])

        )

        .group_by(
            MovimientoStock.articulo_id
        )

        .all()
    )


    datos = []


    for movimiento in movimientos:

        consumido = _float(
            movimiento.consumido
        )

        devuelto = _float(
            movimiento.devuelto
        )

        consumo_neto = max(
            0,
            consumido - devuelto
        )


        if consumo_neto <= 0:
            continue


        articulo = (

            db.query(
                ArticuloStock
            )

            .filter(
                ArticuloStock.id
                == movimiento.articulo_id
            )

            .first()
        )


        if not articulo:
            continue


        datos.append({

            "articulo_id":
                articulo.id,

            "referencia":
                articulo.referencia,

            "nombre":
                articulo.nombre,

            "consumido":
                consumido,

            "devuelto_a_stock":
                devuelto,

            "consumo_neto":
                round(
                    consumo_neto,
                    2
                ),

            "stock_actual":
                _float(
                    articulo.stock_actual
                ),

            "stock_minimo":
                _float(
                    articulo.stock_minimo
                )
        })


    datos.sort(
        key=lambda item:
            item["consumo_neto"],
        reverse=True
    )


    resultado = datos[:limite]


    for posicion, item in enumerate(
        resultado,
        start=1
    ):
        item["posicion"] = posicion


    return resultado


# =========================================================
# REPOSICIÓN
# =========================================================

def resumen_reposicion_stock(
    db: Session,
    limite: int = 50
) -> dict:

    limite = max(
        1,
        min(
            limite or 50,
            100
        )
    )


    articulos = (

        db.query(
            ArticuloStock
        )

        .filter(

            ArticuloStock.activo.is_(True),

            ArticuloStock.stock_actual
            <= ArticuloStock.stock_minimo

        )

        .order_by(
            ArticuloStock.stock_actual.asc()
        )

        .limit(
            limite
        )

        .all()
    )


    resultado = []

    coste_estimado_total = 0.0


    for articulo in articulos:

        actual = _float(
            articulo.stock_actual
        )

        minimo = _float(
            articulo.stock_minimo
        )

        coste = _float(
            articulo.coste
        )


        cantidad_necesaria = max(
            0,
            minimo - actual
        )


        coste_estimado = (
            cantidad_necesaria
            * coste
        )


        coste_estimado_total += (
            coste_estimado
        )


        resultado.append({

            "articulo_id":
                articulo.id,

            "referencia":
                articulo.referencia,

            "nombre":
                articulo.nombre,

            "stock_actual":
                actual,

            "stock_minimo":
                minimo,

            "cantidad_para_minimo":
                round(
                    cantidad_necesaria,
                    2
                ),

            "coste_unitario_actual":
                coste,

            "coste_estimado_reposicion":
                round(
                    coste_estimado,
                    2
                ),

            "proveedor_habitual_id":
                articulo.proveedor_habitual_id
        })


    return {

        "articulos_a_reponer":
            len(resultado),

        "coste_estimado_reposicion":
            round(
                coste_estimado_total,
                2
            ),

        "articulos":
            resultado,

        "criterio": (
            "Reposición mínima necesaria para "
            "alcanzar stock_minimo."
        )
    }


# =========================================================
# RESUMEN DE COMPRAS
# =========================================================

def resumen_compras_stock(
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
                func.distinct(
                    PedidoCompra.id
                )
            ).label(
                "pedidos"
            ),

            func.coalesce(
                func.sum(
                    LineaPedidoCompra
                    .cantidad_pedida
                ),
                0
            ).label(
                "cantidad_pedida"
            ),

            func.coalesce(
                func.sum(
                    LineaPedidoCompra
                    .cantidad_recibida
                ),
                0
            ).label(
                "cantidad_recibida"
            ),

            func.coalesce(
                func.sum(
                    LineaPedidoCompra.coste_unitario
                    *
                    LineaPedidoCompra.cantidad_recibida
                ),
                0
            ).label(
                "coste_recibido_sin_iva"
            )

        )

        .join(
            PedidoCompra,
            LineaPedidoCompra.pedido_id
            == PedidoCompra.id
        )

        .filter(

            PedidoCompra.fecha >= desde,

            PedidoCompra.fecha < hasta

        )

        .one()
    )


    return {

        "periodo": {
            "desde":
                desde.isoformat(),

            "hasta":
                hasta.isoformat()
        },

        "pedidos":
            int(
                resultado.pedidos
                or 0
            ),

        "unidades_pedidas":
            _float(
                resultado.cantidad_pedida
            ),

        "unidades_recibidas":
            _float(
                resultado.cantidad_recibida
            ),

        "unidades_pendientes":
            max(
                0,
                _float(
                    resultado.cantidad_pedida
                )
                -
                _float(
                    resultado.cantidad_recibida
                )
            ),

        "coste_mercancia_recibida_sin_iva":
            _float(
                resultado
                .coste_recibido_sin_iva
            ),

        "criterio": (
            "El coste económico se calcula sobre "
            "cantidad realmente recibida por "
            "coste_unitario histórico."
        )
    }


# =========================================================
# ARTÍCULOS MÁS COMPRADOS
# =========================================================

def articulos_mas_comprados(
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

            LineaPedidoCompra
            .articulo_stock_id
            .label(
                "articulo_id"
            ),

            LineaPedidoCompra
            .referencia
            .label(
                "referencia"
            ),

            LineaPedidoCompra
            .descripcion
            .label(
                "descripcion"
            ),

            func.sum(
                LineaPedidoCompra
                .cantidad_recibida
            ).label(
                "cantidad_recibida"
            ),

            func.sum(
                LineaPedidoCompra.coste_unitario
                *
                LineaPedidoCompra.cantidad_recibida
            ).label(
                "coste_total"
            )

        )

        .join(
            PedidoCompra,
            LineaPedidoCompra.pedido_id
            == PedidoCompra.id
        )

        .filter(

            PedidoCompra.fecha >= desde,

            PedidoCompra.fecha < hasta,

            LineaPedidoCompra
            .cantidad_recibida > 0

        )

        .group_by(

            LineaPedidoCompra
            .articulo_stock_id,

            LineaPedidoCompra
            .referencia,

            LineaPedidoCompra
            .descripcion

        )

        .order_by(
            desc(
                func.sum(
                    LineaPedidoCompra
                    .cantidad_recibida
                )
            )
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

            "articulo_id":
                fila.articulo_id,

            "referencia":
                fila.referencia,

            "descripcion":
                fila.descripcion,

            "cantidad_recibida":
                _float(
                    fila.cantidad_recibida
                ),

            "coste_total_sin_iva":
                _float(
                    fila.coste_total
                )
        }

        for posicion, fila
        in enumerate(
            resultados,
            start=1
        )
    ]


# =========================================================
# EVOLUCIÓN DEL COSTE
# =========================================================

def analizar_coste_articulo(
    db: Session,
    articulo_id: int,
    limite: int = 10
) -> dict:

    if not articulo_id:

        return {
            "encontrado": False
        }


    limite = max(
        2,
        min(
            limite or 10,
            50
        )
    )


    articulo = (

        db.query(
            ArticuloStock
        )

        .filter(
            ArticuloStock.id
            == articulo_id
        )

        .first()
    )


    if not articulo:

        return {
            "encontrado": False
        }


    compras = (

        db.query(

            LineaPedidoCompra.coste_unitario,

            LineaPedidoCompra.cantidad_recibida,

            PedidoCompra.fecha,

            PedidoCompra.numero.label(
                "pedido_numero"
            )

        )

        .join(
            PedidoCompra,
            LineaPedidoCompra.pedido_id
            == PedidoCompra.id
        )

        .filter(

            LineaPedidoCompra.articulo_stock_id
            == articulo_id,

            LineaPedidoCompra.cantidad_recibida
            > 0

        )

        .order_by(
            PedidoCompra.fecha.desc()
        )

        .limit(
            limite
        )

        .all()
    )


    historico = [

        {
            "pedido":
                compra.pedido_numero,

            "fecha": (
                compra.fecha.isoformat()
                if compra.fecha
                else None
            ),

            "coste_unitario":
                _float(
                    compra.coste_unitario
                ),

            "cantidad_recibida":
                _float(
                    compra.cantidad_recibida
                )
        }

        for compra in compras
    ]


    ultimo_coste = (
        _float(
            compras[0].coste_unitario
        )
        if compras
        else None
    )


    coste_anterior = (
        _float(
            compras[1].coste_unitario
        )
        if len(compras) >= 2
        else None
    )


    variacion = None
    variacion_porcentual = None


    if (
        ultimo_coste is not None
        and
        coste_anterior is not None
    ):

        variacion = (
            ultimo_coste
            - coste_anterior
        )


        if coste_anterior != 0:

            variacion_porcentual = (
                variacion
                / coste_anterior
            ) * 100


    return {

        "encontrado": True,

        "articulo": {
            "id":
                articulo.id,

            "referencia":
                articulo.referencia,

            "nombre":
                articulo.nombre,

            "coste_actual":
                _float(
                    articulo.coste
                )
        },

        "numero_compras_analizadas":
            len(compras),

        "ultimo_coste_compra":
            ultimo_coste,

        "coste_compra_anterior":
            coste_anterior,

        "variacion_ultimo_coste":
            (
                round(
                    variacion,
                    2
                )
                if variacion is not None
                else None
            ),

        "variacion_porcentual":
            (
                round(
                    variacion_porcentual,
                    2
                )
                if variacion_porcentual is not None
                else None
            ),

        "tendencia": (
            "SUBE"
            if variacion is not None
            and variacion > 0

            else "BAJA"
            if variacion is not None
            and variacion < 0

            else "IGUAL"
            if variacion is not None

            else "SIN_DATOS_SUFICIENTES"
        ),

        "historico":
            historico
    }
"""Herramientas IA de consumo, valoración y reposición de almacén."""
