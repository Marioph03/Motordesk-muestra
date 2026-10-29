"""Catálogo y ejecutor central de tools permitidas para MotorDesk AI.

Cada tool se autoriza y audita antes y después de su ejecución. No añadas
accesos SQL genéricos: las herramientas deben representar una operación concreta.
"""

from sqlalchemy.orm import Session

from app.ai.security.ai_permissions import (
    AIPermissionError,
    WORKFLOW_PERMISSIONS,
    comprobar_permiso_tool,
    comprobar_permisos_workflow,
)
from app.ai.audit.audit_service import (
    TipoEventoAI,
    registrar_evento_ai,
)

from app.ai.audit.audit_service import (
    TipoEventoAI,
    registrar_evento_ai,
    sanitizar_auditoria
)

from app.ai.tools.clientes_tools import (
    CLIENTES_TOOLS,
    buscar_cliente
)

from app.ai.tools.vehiculos_tools import (
    VEHICULOS_TOOLS,
    buscar_vehiculo,
    obtener_vehiculos_cliente
)

from app.ai.tools.analytics_tools import (
    ANALYTICS_TOOLS,
    resumen_facturacion,
    comparar_facturacion,
    resumen_pendiente_cobro,
    ranking_clientes_facturacion
)
from app.ai.tools.cobros_tools import (
    COBROS_TOOLS,
    resumen_cobros,
    resumen_deuda_pendiente,
    obtener_situacion_cobro_factura,
    obtener_deuda_cliente,
    ranking_clientes_deuda,
)
from app.ai.tools.taller_analytics_tools import (
    TALLER_ANALYTICS_TOOLS,
    resumen_actividad_taller,
    tiempo_medio_reparacion,
    vehiculos_mas_recurrentes,
    ordenes_abiertas_antiguas,
    ranking_clientes_visitas_taller,
)
from app.ai.tools.stock_analytics_tools import (
    STOCK_ANALYTICS_TOOLS,
    resumen_valor_stock,
    articulos_mas_consumidos,
    resumen_reposicion_stock,
    resumen_compras_stock,
    articulos_mas_comprados,
    analizar_coste_articulo,
)
from app.ai.tools.insights_tools import (
    INSIGHTS_TOOLS,
    resumen_ejecutivo,
)
from app.ai.tools.actions_tools import (
    ACTIONS_TOOLS,
    proponer_crear_cita,
    proponer_crear_orden,
    proponer_crear_cliente,
    proponer_crear_vehiculo,
    proponer_alta_cliente_vehiculo_cita,
    proponer_alta_cliente_vehiculo_orden,
)

from app.ai.tools.dashboard_tools import (
    DASHBOARD_TOOLS,
    obtener_dashboard
)
from app.ai.tools.ordenes_tools import (
    ORDENES_TOOLS,
    buscar_orden,
    listar_ordenes,
    obtener_detalle_orden,
    obtener_ordenes_cliente,
    obtener_ordenes_vehiculo
)
from app.ai.tools.facturas_tools import (
    FACTURAS_TOOLS,
    buscar_factura,
    listar_facturas,
    obtener_detalle_factura,
    obtener_facturas_cliente,
    obtener_facturas_vehiculo,
    obtener_facturas_orden,
)
from app.ai.tools.agenda_tools import (
    AGENDA_TOOLS,
    listar_citas,
    obtener_detalle_cita,
    obtener_citas_cliente,
    obtener_citas_vehiculo,
)
from app.ai.tools.stock_tools import (
    STOCK_TOOLS,
    buscar_articulo_stock,
    obtener_detalle_stock,
    listar_stock_bajo,
    listar_articulos_sin_stock,
    obtener_movimientos_stock,
)
from app.ai.tools.proveedores_tools import (
    PROVEEDORES_TOOLS,
    buscar_proveedor,
    obtener_detalle_proveedor,
    listar_proveedores,
    obtener_articulos_proveedor,
    obtener_reposicion_proveedor,
)
from app.ai.tools.compras_tools import (
    COMPRAS_TOOLS,
    buscar_pedido_compra,
    listar_pedidos_compra,
    obtener_detalle_pedido_compra,
    buscar_albaran_proveedor,
    listar_albaranes_proveedor,
    obtener_detalle_albaran_proveedor,
    listar_devoluciones_proveedor,
    obtener_detalle_devolucion_proveedor,
)
from app.ai.tools.garantias_tools import (
    GARANTIAS_TOOLS,
    listar_garantias,
    obtener_detalle_garantia,
    obtener_garantias_vehiculo,
    obtener_garantias_cliente,
)


# =========================================================
# TODAS LAS TOOLS DISPONIBLES PARA EL MODELO
# =========================================================

MOTOR_AI_TOOLS = [

    *CLIENTES_TOOLS,

    *VEHICULOS_TOOLS,

    *DASHBOARD_TOOLS,

    *ORDENES_TOOLS,

    *FACTURAS_TOOLS,

    *AGENDA_TOOLS,

    *STOCK_TOOLS,

    *PROVEEDORES_TOOLS,

    *COMPRAS_TOOLS,

    *GARANTIAS_TOOLS,

    # Analytics
    *ANALYTICS_TOOLS,

    # Cobros
    *COBROS_TOOLS,

    # Analytics del taller
    *TALLER_ANALYTICS_TOOLS,

    # Analytics de stock y compras
    *STOCK_ANALYTICS_TOOLS,

    # Insights
    *INSIGHTS_TOOLS,

    # Acciones seguras: solo propuestas, nunca ejecutan directamente.
    *ACTIONS_TOOLS,

]


# =========================================================
# EJECUCIÓN
# =========================================================

def _ejecutar_tool_interna(
    nombre: str,
    argumentos: dict,
    db: Session,
    usuario,
):

    usuario_id = usuario.id

    if nombre == "buscar_cliente":

        return buscar_cliente(

            db=db,

            texto=argumentos.get(
                "texto",
                ""
            )

        )


    if nombre == "buscar_vehiculo":

        return buscar_vehiculo(

            db=db,

            texto=argumentos.get(
                "texto",
                ""
            )

        )


    if (
        nombre
        == "obtener_vehiculos_cliente"
    ):

        return obtener_vehiculos_cliente(

            db=db,

            cliente_id=argumentos.get(
                "cliente_id"
            )

        )


    if nombre == "obtener_dashboard":

        return obtener_dashboard(
            db=db
        )


    if nombre == "buscar_orden":

        return buscar_orden(
            db=db,
            texto=argumentos.get(
                "texto",
                ""
            )
        )


    if nombre == "listar_ordenes":

        return listar_ordenes(
            db=db,
            estado=argumentos.get(
                "estado"
            ),
            tipo=argumentos.get(
                "tipo"
            ),
            limite=argumentos.get(
                "limite",
                20
            )
        )


    if nombre == "obtener_detalle_orden":

        return obtener_detalle_orden(
            db=db,
            orden_id=argumentos.get(
                "orden_id"
            )
        )


    if nombre == "obtener_ordenes_cliente":

        return obtener_ordenes_cliente(
            db=db,
            cliente_id=argumentos.get(
                "cliente_id"
            )
        )


    if nombre == "obtener_ordenes_vehiculo":

        return obtener_ordenes_vehiculo(
            db=db,
            vehiculo_id=argumentos.get(
                "vehiculo_id"
            )
        )


    # Facturas: consultas exclusivamente de lectura.
    if nombre == "buscar_factura":

        return buscar_factura(
            db=db,
            texto=argumentos.get("texto", "")
        )


    if nombre == "listar_facturas":

        return listar_facturas(
            db=db,
            estado=argumentos.get("estado"),
            estado_cobro=argumentos.get("estado_cobro"),
            tipo_factura=argumentos.get("tipo_factura"),
            es_prueba=argumentos.get("es_prueba"),
            limite=argumentos.get("limite", 20)
        )


    if nombre == "obtener_detalle_factura":

        return obtener_detalle_factura(
            db=db,
            factura_id=argumentos.get("factura_id")
        )


    if nombre == "obtener_facturas_cliente":

        return obtener_facturas_cliente(
            db=db,
            cliente_id=argumentos.get("cliente_id")
        )


    if nombre == "obtener_facturas_vehiculo":

        return obtener_facturas_vehiculo(
            db=db,
            vehiculo_id=argumentos.get("vehiculo_id")
        )


    if nombre == "obtener_facturas_orden":

        return obtener_facturas_orden(
            db=db,
            orden_id=argumentos.get("orden_id")
        )


    # Agenda: consultas exclusivamente de lectura.
    if nombre == "listar_citas":

        return listar_citas(
            db=db,
            fecha_desde=argumentos.get("fecha_desde"),
            fecha_hasta=argumentos.get("fecha_hasta"),
            estado=argumentos.get("estado"),
            limite=argumentos.get("limite", 50)
        )


    if nombre == "obtener_detalle_cita":

        return obtener_detalle_cita(
            db=db,
            cita_id=argumentos.get("cita_id")
        )


    if nombre == "obtener_citas_cliente":

        return obtener_citas_cliente(
            db=db,
            cliente_id=argumentos.get("cliente_id"),
            solo_futuras=argumentos.get("solo_futuras", False)
        )


    if nombre == "obtener_citas_vehiculo":

        return obtener_citas_vehiculo(
            db=db,
            vehiculo_id=argumentos.get("vehiculo_id"),
            solo_futuras=argumentos.get("solo_futuras", False)
        )


    # Stock / almacén: consultas exclusivamente de lectura.
    if nombre == "buscar_articulo_stock":

        return buscar_articulo_stock(
            db=db,
            texto=argumentos.get("texto", ""),
            solo_activos=argumentos.get("solo_activos", True)
        )


    if nombre == "obtener_detalle_stock":

        return obtener_detalle_stock(
            db=db,
            articulo_id=argumentos.get("articulo_id")
        )


    if nombre == "listar_stock_bajo":

        return listar_stock_bajo(
            db=db,
            limite=argumentos.get("limite", 50)
        )


    if nombre == "listar_articulos_sin_stock":

        return listar_articulos_sin_stock(
            db=db,
            limite=argumentos.get("limite", 50)
        )


    if nombre == "obtener_movimientos_stock":

        return obtener_movimientos_stock(
            db=db,
            articulo_id=argumentos.get("articulo_id"),
            limite=argumentos.get("limite", 30)
        )


    # Proveedores: consultas exclusivamente de lectura.
    if nombre == "buscar_proveedor":
        return buscar_proveedor(db=db, texto=argumentos.get("texto", ""), solo_activos=argumentos.get("solo_activos", True))

    if nombre == "obtener_detalle_proveedor":
        return obtener_detalle_proveedor(db=db, proveedor_id=argumentos.get("proveedor_id"))

    if nombre == "listar_proveedores":
        return listar_proveedores(db=db, solo_activos=argumentos.get("solo_activos", True), limite=argumentos.get("limite", 50))

    if nombre == "obtener_articulos_proveedor":
        return obtener_articulos_proveedor(db=db, proveedor_id=argumentos.get("proveedor_id"), solo_activos=argumentos.get("solo_activos", True))

    if nombre == "obtener_reposicion_proveedor":
        return obtener_reposicion_proveedor(db=db, proveedor_id=argumentos.get("proveedor_id"))


    # Compras: consultas exclusivamente de lectura.
    if nombre == "buscar_pedido_compra":
        return buscar_pedido_compra(db=db, texto=argumentos.get("texto", ""))
    if nombre == "listar_pedidos_compra":
        return listar_pedidos_compra(db=db, proveedor_id=argumentos.get("proveedor_id"), estado=argumentos.get("estado"), limite=argumentos.get("limite", 50))
    if nombre == "obtener_detalle_pedido_compra":
        return obtener_detalle_pedido_compra(db=db, pedido_id=argumentos.get("pedido_id"))
    if nombre == "buscar_albaran_proveedor":
        return buscar_albaran_proveedor(db=db, texto=argumentos.get("texto", ""))
    if nombre == "listar_albaranes_proveedor":
        return listar_albaranes_proveedor(db=db, proveedor_id=argumentos.get("proveedor_id"), limite=argumentos.get("limite", 50))
    if nombre == "obtener_detalle_albaran_proveedor":
        return obtener_detalle_albaran_proveedor(db=db, albaran_id=argumentos.get("albaran_id"))
    if nombre == "listar_devoluciones_proveedor":
        return listar_devoluciones_proveedor(db=db, proveedor_id=argumentos.get("proveedor_id"), estado=argumentos.get("estado"), resolucion=argumentos.get("resolucion"), limite=argumentos.get("limite", 50))
    if nombre == "obtener_detalle_devolucion_proveedor":
        return obtener_detalle_devolucion_proveedor(db=db, devolucion_id=argumentos.get("devolucion_id"))


    # Garantías: consultas exclusivamente de lectura.
    if nombre == "listar_garantias":
        return listar_garantias(db=db, estado=argumentos.get("estado"), limite=argumentos.get("limite", 50))
    if nombre == "obtener_detalle_garantia":
        return obtener_detalle_garantia(db=db, garantia_id=argumentos.get("garantia_id"))
    if nombre == "obtener_garantias_vehiculo":
        return obtener_garantias_vehiculo(db=db, vehiculo_id=argumentos.get("vehiculo_id"))
    if nombre == "obtener_garantias_cliente":
        return obtener_garantias_cliente(db=db, cliente_id=argumentos.get("cliente_id"))


    # Analytics: agregados de solo lectura sobre facturación real.
    if nombre == "resumen_facturacion":
        return resumen_facturacion(
            db=db,
            fecha_desde=argumentos.get("fecha_desde"),
            fecha_hasta=argumentos.get("fecha_hasta")
        )

    if nombre == "comparar_facturacion":
        return comparar_facturacion(
            db=db,
            periodo_1_desde=argumentos.get("periodo_1_desde"),
            periodo_1_hasta=argumentos.get("periodo_1_hasta"),
            periodo_2_desde=argumentos.get("periodo_2_desde"),
            periodo_2_hasta=argumentos.get("periodo_2_hasta")
        )

    if nombre == "resumen_pendiente_cobro":
        return resumen_pendiente_cobro(db=db)

    if nombre == "ranking_clientes_facturacion":
        return ranking_clientes_facturacion(
            db=db,
            fecha_desde=argumentos.get("fecha_desde"),
            fecha_hasta=argumentos.get("fecha_hasta"),
            limite=argumentos.get("limite", 10)
        )


    # Analytics - cobros: consultas exclusivamente de lectura.
    if nombre == "resumen_cobros":
        return resumen_cobros(
            db=db,
            fecha_desde=argumentos.get("fecha_desde"),
            fecha_hasta=argumentos.get("fecha_hasta")
        )

    if nombre == "resumen_deuda_pendiente":
        return resumen_deuda_pendiente(db=db)

    if nombre == "obtener_situacion_cobro_factura":
        return obtener_situacion_cobro_factura(
            db=db,
            factura_id=argumentos.get("factura_id")
        )

    if nombre == "obtener_deuda_cliente":
        return obtener_deuda_cliente(
            db=db,
            cliente_id=argumentos.get("cliente_id")
        )

    if nombre == "ranking_clientes_deuda":
        return ranking_clientes_deuda(
            db=db,
            limite=argumentos.get("limite", 10)
        )


    # Analytics - taller: consultas exclusivamente de lectura.
    if nombre == "resumen_actividad_taller":
        return resumen_actividad_taller(
            db=db,
            fecha_desde=argumentos.get("fecha_desde"),
            fecha_hasta=argumentos.get("fecha_hasta")
        )

    if nombre == "tiempo_medio_reparacion":
        return tiempo_medio_reparacion(
            db=db,
            fecha_desde=argumentos.get("fecha_desde"),
            fecha_hasta=argumentos.get("fecha_hasta")
        )

    if nombre == "vehiculos_mas_recurrentes":
        return vehiculos_mas_recurrentes(
            db=db,
            fecha_desde=argumentos.get("fecha_desde"),
            fecha_hasta=argumentos.get("fecha_hasta"),
            limite=argumentos.get("limite", 10)
        )

    if nombre == "ordenes_abiertas_antiguas":
        return ordenes_abiertas_antiguas(
            db=db,
            limite=argumentos.get("limite", 10)
        )

    if nombre == "ranking_clientes_visitas_taller":
        return ranking_clientes_visitas_taller(
            db=db,
            fecha_desde=argumentos.get("fecha_desde"),
            fecha_hasta=argumentos.get("fecha_hasta"),
            limite=argumentos.get("limite", 10)
        )


    # Analytics - stock / compras: consultas exclusivamente de lectura.
    if nombre == "resumen_valor_stock":
        return resumen_valor_stock(db=db)

    if nombre == "articulos_mas_consumidos":
        return articulos_mas_consumidos(
            db=db,
            fecha_desde=argumentos.get("fecha_desde"),
            fecha_hasta=argumentos.get("fecha_hasta"),
            limite=argumentos.get("limite", 10)
        )

    if nombre == "resumen_reposicion_stock":
        return resumen_reposicion_stock(db=db, limite=argumentos.get("limite", 50))

    if nombre == "resumen_compras_stock":
        return resumen_compras_stock(
            db=db,
            fecha_desde=argumentos.get("fecha_desde"),
            fecha_hasta=argumentos.get("fecha_hasta")
        )

    if nombre == "articulos_mas_comprados":
        return articulos_mas_comprados(
            db=db,
            fecha_desde=argumentos.get("fecha_desde"),
            fecha_hasta=argumentos.get("fecha_hasta"),
            limite=argumentos.get("limite", 10)
        )

    if nombre == "analizar_coste_articulo":
        return analizar_coste_articulo(
            db=db,
            articulo_id=argumentos.get("articulo_id"),
            limite=argumentos.get("limite", 10)
        )


    # MotorDesk Insights: resumen global calculado en el backend.
    if nombre == "resumen_ejecutivo":
        return resumen_ejecutivo(
            db=db,
            fecha_desde=argumentos.get("fecha_desde"),
            fecha_hasta=argumentos.get("fecha_hasta"),
            comparacion_desde=argumentos.get("comparacion_desde"),
            comparacion_hasta=argumentos.get("comparacion_hasta")
        )


    # Actions: la tool crea una propuesta; la confirmación se hace fuera del LLM.
    if nombre == "proponer_crear_cita":
        if usuario_id is None:
            raise PermissionError("No hay usuario autenticado.")
        return proponer_crear_cita(db=db, argumentos=argumentos, usuario_id=usuario_id)


    if nombre == "proponer_crear_orden":
        if usuario_id is None:
            raise PermissionError("No hay usuario autenticado.")
        return proponer_crear_orden(
            db=db,
            argumentos=argumentos,
            usuario_id=usuario_id,
        )


    if nombre == "proponer_crear_cliente":
        if usuario_id is None:
            raise PermissionError("No hay usuario autenticado.")
        return proponer_crear_cliente(
            db=db,
            argumentos=argumentos,
            usuario_id=usuario_id,
        )


    if nombre == "proponer_crear_vehiculo":
        if usuario_id is None:
            raise PermissionError("No hay usuario autenticado.")
        return proponer_crear_vehiculo(
            db=db,
            argumentos=argumentos,
            usuario_id=usuario_id,
        )


    if nombre == "proponer_alta_cliente_vehiculo_cita":
        if usuario_id is None:
            raise PermissionError("No hay usuario autenticado.")
        workflow = proponer_alta_cliente_vehiculo_cita(
            db=db,
            usuario_id=usuario_id,
            datos=argumentos,
        )
        return {
            "workflow_pendiente": True,
            "workflow_id": workflow.id,
            "tipo": workflow.tipo.value,
            "resumen": workflow.resumen,
            "pasos": [
                {
                    "orden": paso.orden,
                    "tipo": paso.tipo.value,
                    "resumen": paso.resumen,
                }
                for paso in workflow.pasos
            ],
            "instruccion": (
                "No se ha realizado ningún cambio. El usuario debe "
                "confirmar el workflow completo desde MotorDesk."
            ),
        }


    if nombre == "proponer_alta_cliente_vehiculo_orden":
        if usuario_id is None:
            raise PermissionError("No hay usuario autenticado.")
        workflow = proponer_alta_cliente_vehiculo_orden(
            db=db,
            usuario_id=usuario_id,
            datos=argumentos,
        )
        return {
            "workflow_pendiente": True,
            "workflow_id": workflow.id,
            "tipo": workflow.tipo.value,
            "resumen": workflow.resumen,
            "pasos": [
                {
                    "orden": paso.orden,
                    "tipo": paso.tipo.value,
                    "resumen": paso.resumen,
                }
                for paso in workflow.pasos
            ],
            "instruccion": (
                "No se ha realizado ningún cambio. El usuario debe "
                "confirmar el workflow completo desde MotorDesk."
            ),
        }


    raise ValueError(
        (
            "MotorDesk AI intentó utilizar "
            f"una herramienta desconocida: {nombre}"
        )
    )


def ejecutar_tool(
    nombre: str,
    argumentos: dict,
    db: Session,
    usuario,
):
    """Ejecuta una tool con control de permisos y trazabilidad centralizada."""

    try:
        comprobar_permiso_tool(db, usuario, nombre)
        if nombre in WORKFLOW_PERMISSIONS:
            comprobar_permisos_workflow(db, usuario, nombre)

        registrar_evento_ai(
            db=db,
            usuario_id=usuario.id,
            tipo_evento=TipoEventoAI.TOOL_CALL,
            recurso=nombre,
            descripcion=f"Ejecución de tool {nombre}.",
            datos=argumentos,
        )

        resultado = _ejecutar_tool_interna(
            nombre=nombre,
            argumentos=argumentos,
            db=db,
            usuario=usuario,
        )

        registrar_evento_ai(
            db=db,
            usuario_id=usuario.id,
            tipo_evento=TipoEventoAI.TOOL_OK,
            recurso=nombre,
            descripcion=f"Tool {nombre} ejecutada correctamente.",
            resultado=resultado,
        )

        return resultado

    except AIPermissionError as error:
        registrar_evento_ai(
            db=db,
            usuario_id=usuario.id,
            tipo_evento=TipoEventoAI.PERMISO_DENEGADO,
            recurso=nombre,
            descripcion="Intento de ejecutar una herramienta sin permisos suficientes.",
            exitoso=False,
            error=str(error),
        )
        raise

    except Exception as error:
        registrar_evento_ai(
            db=db,
            usuario_id=usuario.id,
            tipo_evento=TipoEventoAI.TOOL_ERROR,
            recurso=nombre,
            descripcion=f"Error ejecutando tool {nombre}.",
            datos=argumentos,
            exitoso=False,
            error=str(error),
        )
        raise
