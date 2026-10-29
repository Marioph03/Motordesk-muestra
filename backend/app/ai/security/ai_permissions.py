from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.services.permisos_service import PermisosService


class AIPermissionError(PermissionError):
    pass


@dataclass(frozen=True)
class ToolPermission:
    permiso: str | None = None


def _asignar(permisos: dict[str, ToolPermission], nombres: list[str], permiso: str) -> None:
    for nombre in nombres:
        permisos[nombre] = ToolPermission(permiso)


TOOL_PERMISSIONS: dict[str, ToolPermission] = {}

_asignar(TOOL_PERMISSIONS, [
    "buscar_cliente",
], "clientes.ver")
_asignar(TOOL_PERMISSIONS, [
    "buscar_vehiculo", "obtener_vehiculos_cliente",
], "vehiculos.ver")
_asignar(TOOL_PERMISSIONS, [
    "buscar_orden", "listar_ordenes", "obtener_detalle_orden",
    "obtener_ordenes_cliente", "obtener_ordenes_vehiculo",
    "listar_garantias", "obtener_detalle_garantia",
    "obtener_garantias_vehiculo", "obtener_garantias_cliente",
    "resumen_actividad_taller", "tiempo_medio_reparacion",
    "vehiculos_mas_recurrentes", "ordenes_abiertas_antiguas",
    "ranking_clientes_visitas_taller",
], "ordenes.ver")
_asignar(TOOL_PERMISSIONS, [
    "buscar_factura", "listar_facturas", "obtener_detalle_factura",
    "obtener_facturas_cliente", "obtener_facturas_vehiculo",
    "obtener_facturas_orden", "resumen_facturacion", "comparar_facturacion",
    "resumen_pendiente_cobro", "ranking_clientes_facturacion",
    "resumen_cobros", "resumen_deuda_pendiente",
    "obtener_situacion_cobro_factura", "obtener_deuda_cliente",
    "ranking_clientes_deuda",
], "facturas.ver")
_asignar(TOOL_PERMISSIONS, [
    "listar_citas", "obtener_detalle_cita", "obtener_citas_cliente",
    "obtener_citas_vehiculo",
], "agenda.ver")
_asignar(TOOL_PERMISSIONS, [
    "buscar_articulo_stock", "obtener_detalle_stock", "listar_stock_bajo",
    "listar_articulos_sin_stock", "obtener_movimientos_stock",
    "resumen_valor_stock", "articulos_mas_consumidos",
    "resumen_reposicion_stock", "resumen_compras_stock",
    "articulos_mas_comprados", "analizar_coste_articulo",
], "stock.ver")
_asignar(TOOL_PERMISSIONS, [
    "buscar_proveedor", "obtener_detalle_proveedor", "listar_proveedores",
    "obtener_articulos_proveedor", "obtener_reposicion_proveedor",
], "proveedores.ver")
_asignar(TOOL_PERMISSIONS, [
    "buscar_pedido_compra", "listar_pedidos_compra", "obtener_detalle_pedido_compra",
    "buscar_albaran_proveedor", "listar_albaranes_proveedor",
    "obtener_detalle_albaran_proveedor", "listar_devoluciones_proveedor",
    "obtener_detalle_devolucion_proveedor",
], "compras.ver")
_asignar(TOOL_PERMISSIONS, ["obtener_dashboard", "resumen_ejecutivo"], "informes.ver")
_asignar(TOOL_PERMISSIONS, ["proponer_crear_cliente"], "clientes.crear")
_asignar(TOOL_PERMISSIONS, ["proponer_crear_vehiculo"], "vehiculos.crear")
_asignar(TOOL_PERMISSIONS, ["proponer_crear_cita"], "agenda.crear")
_asignar(TOOL_PERMISSIONS, ["proponer_crear_orden"], "ordenes.crear")

WORKFLOW_PERMISSIONS: dict[str, list[str]] = {
    "proponer_alta_cliente_vehiculo_cita": [
        "clientes.crear", "vehiculos.crear", "agenda.crear",
    ],
    "proponer_alta_cliente_vehiculo_orden": [
        "clientes.crear", "vehiculos.crear", "ordenes.crear",
    ],
}

WORKFLOW_TYPE_PERMISSIONS: dict[str, list[str]] = {
    "ALTA_CLIENTE_VEHICULO_CITA": WORKFLOW_PERMISSIONS[
        "proponer_alta_cliente_vehiculo_cita"
    ],
    "ALTA_CLIENTE_VEHICULO_ORDEN": WORKFLOW_PERMISSIONS[
        "proponer_alta_cliente_vehiculo_orden"
    ],
}

ACTION_PERMISSIONS = {
    "CREAR_CLIENTE": "clientes.crear",
    "CREAR_VEHICULO": "vehiculos.crear",
    "CREAR_CITA": "agenda.crear",
    "CREAR_ORDEN": "ordenes.crear",
}


def _valor(tipo) -> str:
    return str(getattr(tipo, "value", tipo))


def usuario_tiene_permiso(db: Session, usuario, permiso: str) -> bool:
    if usuario is None or not getattr(usuario, "activo", False):
        return False
    return PermisosService.usuario_tiene_permiso(db, usuario, permiso)


def comprobar_permiso_tool(db: Session, usuario, nombre_tool: str) -> None:
    configuracion = TOOL_PERMISSIONS.get(nombre_tool)
    if configuracion is None:
        # Los workflows se permiten aquí y se comprueban con su lista completa.
        if nombre_tool not in WORKFLOW_PERMISSIONS:
            raise AIPermissionError("La herramienta de IA no está autorizada.")
        return
    if configuracion.permiso and not usuario_tiene_permiso(
        db, usuario, configuracion.permiso
    ):
        raise AIPermissionError("No tienes permiso para realizar esta acción en MotorDesk.")


def comprobar_permisos_workflow(db: Session, usuario, nombre_tool: str) -> None:
    permisos = WORKFLOW_PERMISSIONS.get(nombre_tool)
    if permisos is None:
        raise AIPermissionError("Workflow de IA no autorizado.")
    if any(not usuario_tiene_permiso(db, usuario, permiso) for permiso in permisos):
        raise AIPermissionError(
            "No tienes todos los permisos necesarios para realizar esta operación."
        )


def comprobar_permiso_action(db: Session, usuario, tipo_action) -> None:
    permiso = ACTION_PERMISSIONS.get(_valor(tipo_action))
    if permiso is None:
        raise AIPermissionError("Action de IA no autorizada.")
    if not usuario_tiene_permiso(db, usuario, permiso):
        raise AIPermissionError(
            "Ya no tienes permiso para confirmar esta operación."
        )


def comprobar_permiso_tipo_workflow(db: Session, usuario, tipo_workflow) -> None:
    permisos = WORKFLOW_TYPE_PERMISSIONS.get(_valor(tipo_workflow))
    if permisos is None:
        raise AIPermissionError("Workflow no autorizado.")
    if any(not usuario_tiene_permiso(db, usuario, permiso) for permiso in permisos):
        raise AIPermissionError(
            "Ya no tienes todos los permisos necesarios para confirmar esta operación."
        )


def filtrar_tools_usuario(db: Session, usuario, tools: list[dict]) -> list[dict]:
    permitidas = []
    for tool in tools:
        nombre = tool.get("function", {}).get("name")
        if not nombre:
            continue
        try:
            comprobar_permiso_tool(db, usuario, nombre)
            if nombre in WORKFLOW_PERMISSIONS:
                comprobar_permisos_workflow(db, usuario, nombre)
            permitidas.append(tool)
        except AIPermissionError:
            continue
    return permitidas
"""Puente entre permisos de MotorDesk y herramientas disponibles para IA."""
