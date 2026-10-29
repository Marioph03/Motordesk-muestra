"""Orquestador de MotorDesk AI: memoria temporal, tools seguras y proveedor."""

import json
import os
import unicodedata
from datetime import datetime

from sqlalchemy.orm import Session

from app.ai.groq_provider import GroqProvider, AIProviderToolUseError
from app.ai.memory.context_extractor import extraer_contexto
from app.ai.memory.conversation_store import conversation_store
from app.ai.motor_ai_prompt import MOTOR_AI_SYSTEM_PROMPT
from app.ai.tool_registry import MOTOR_AI_TOOLS, ejecutar_tool
from app.ai.security.ai_permissions import filtrar_tools_usuario


_TOOLS_POR_AMBITO = {
    "clientes": {
        "buscar_cliente",
    },
    "vehiculos": {
        "buscar_vehiculo",
        "obtener_vehiculos_cliente",
    },
    "ordenes": {
        "buscar_orden", "listar_ordenes", "obtener_detalle_orden",
        "obtener_ordenes_cliente", "obtener_ordenes_vehiculo",
        "resumen_actividad_taller", "tiempo_medio_reparacion",
        "vehiculos_mas_recurrentes", "ordenes_abiertas_antiguas",
        "ranking_clientes_visitas_taller",
    },
    "facturas": {
        "buscar_factura", "listar_facturas", "obtener_detalle_factura",
        "obtener_facturas_cliente", "obtener_facturas_vehiculo",
        "obtener_facturas_orden", "resumen_facturacion",
        "comparar_facturacion", "resumen_pendiente_cobro",
        "ranking_clientes_facturacion", "resumen_cobros",
        "resumen_deuda_pendiente", "obtener_situacion_cobro_factura",
        "obtener_deuda_cliente", "ranking_clientes_deuda",
    },
    "agenda": {
        "listar_citas", "obtener_detalle_cita", "obtener_citas_cliente",
        "obtener_citas_vehiculo",
    },
    "stock": {
        "buscar_articulo_stock", "obtener_detalle_stock", "listar_stock_bajo",
        "listar_articulos_sin_stock", "obtener_movimientos_stock",
        "resumen_valor_stock", "articulos_mas_consumidos",
        "resumen_reposicion_stock", "resumen_compras_stock",
        "articulos_mas_comprados", "analizar_coste_articulo",
    },
    "compras": {
        "buscar_proveedor", "obtener_detalle_proveedor", "listar_proveedores",
        "obtener_articulos_proveedor", "obtener_reposicion_proveedor",
        "buscar_pedido_compra", "listar_pedidos_compra", "obtener_detalle_pedido_compra",
        "buscar_albaran_proveedor", "listar_albaranes_proveedor",
        "obtener_detalle_albaran_proveedor", "listar_devoluciones_proveedor",
        "obtener_detalle_devolucion_proveedor",
    },
    "garantias": {
        "listar_garantias", "obtener_detalle_garantia",
        "obtener_garantias_vehiculo", "obtener_garantias_cliente",
    },
    "general": {"obtener_dashboard", "resumen_ejecutivo"},
}


class MotorAIService:
    """Coordina una consulta IA sin permitir acceso directo del modelo a la BD."""

    def __init__(self):
        self.provider = GroqProvider()

    @staticmethod
    def _texto_contexto(usuario_id: int) -> tuple[object, str]:
        contexto = conversation_store.obtener(usuario_id)
        valores = []
        for etiqueta, valor in (
            ("cliente_id actual", contexto.cliente_id),
            ("vehiculo_id actual", contexto.vehiculo_id),
            ("matrícula actual", contexto.matricula),
            ("orden_id actual", contexto.orden_id),
            ("factura_id actual", contexto.factura_id),
            ("cita_id actual", contexto.cita_id),
        ):
            if valor is not None:
                valores.append(f"{etiqueta}: {valor}")
        return contexto, "\n".join(valores) or "Sin entidades seleccionadas."

    @staticmethod
    def _normalizar_texto(texto: str) -> str:
        return "".join(
            caracter
            for caracter in unicodedata.normalize("NFD", texto.lower())
            if unicodedata.category(caracter) != "Mn"
        )

    @classmethod
    def _seleccionar_tools(cls, mensaje: str, tools: list[dict]) -> list[dict]:
        """Envía al proveedor solo las herramientas plausibles para la consulta.

        Mandar todas las definiciones consume más tokens que una conversación
        normal y puede superar el límite TPM del proveedor.
        """
        texto = cls._normalizar_texto(mensaje)
        ambitos: set[str] = set()

        def contiene(*terminos: str) -> bool:
            return any(termino in texto for termino in terminos)

        if contiene("cliente", "dni", "nif"):
            ambitos.add("clientes")
        if contiene("vehiculo", "matricula", "bastidor", "coche", "auto"):
            ambitos.add("vehiculos")
        if contiene("orden", "reparacion", "averia", "taller"):
            ambitos.add("ordenes")
        if contiene("factura", "facturacion", "facturado", "cobro", "cobrado", "deuda", "pago"):
            ambitos.add("facturas")
        if contiene("cita", "agenda", "calendario"):
            ambitos.add("agenda")
        if contiene("stock", "almacen", "recambio", "articulo", "pieza"):
            ambitos.add("stock")
        if contiene("proveedor", "compra", "pedido", "albaran", "devolucion"):
            ambitos.add("compras")
        if contiene("garantia"):
            ambitos.add("garantias")
        if contiene("dashboard", "resumen ejecutivo", "como va", "vision general", "que deberia revisar"):
            ambitos.add("general")

        crear = contiene("crear", "alta", "nuevo", "nueva", "registrar", "abrir")
        nombres: set[str] = set()
        for ambito in ambitos:
            nombres.update(_TOOLS_POR_AMBITO[ambito])

        if crear:
            if {"clientes", "vehiculos", "agenda"}.issubset(ambitos):
                nombres.add("proponer_alta_cliente_vehiculo_cita")
            elif {"clientes", "vehiculos", "ordenes"}.issubset(ambitos):
                nombres.add("proponer_alta_cliente_vehiculo_orden")
            else:
                acciones = {
                    "clientes": "proponer_crear_cliente",
                    "vehiculos": "proponer_crear_vehiculo",
                    "agenda": "proponer_crear_cita",
                    "ordenes": "proponer_crear_orden",
                }
                for ambito, accion in acciones.items():
                    if ambito in ambitos:
                        nombres.add(accion)

        # Una conversación sin intención operativa (por ejemplo, "hola") no
        # necesita schemas de herramientas.
        if not nombres:
            return []

        max_tools = max(1, min(int(os.getenv("GROQ_MAX_TOOLS_POR_CONSULTA", "18")), 24))
        seleccionadas = [
            tool for tool in tools
            if tool.get("function", {}).get("name") in nombres
        ]
        return seleccionadas[:max_tools]

    @staticmethod
    def _mensajes_memoria(contexto) -> list[dict]:
        limite_mensajes = max(0, min(int(os.getenv("GROQ_MEMORY_MESSAGES", "4")), 8))
        limite_caracteres = max(0, int(os.getenv("GROQ_MEMORY_MAX_CHARS", "2400")))
        restantes = limite_caracteres
        mensajes = []
        for item in reversed(contexto.mensajes[-limite_mensajes:]):
            contenido = item.contenido[-restantes:] if restantes else ""
            if contenido:
                mensajes.append({"role": item.rol, "content": contenido})
                restantes -= len(contenido)
            if restantes <= 0:
                break
        return list(reversed(mensajes))

    @staticmethod
    def _contenido_tool(resultado) -> str:
        contenido = json.dumps(resultado, ensure_ascii=False, default=str)
        limite = max(500, int(os.getenv("GROQ_TOOL_RESULT_MAX_CHARS", "5000")))
        if len(contenido) <= limite:
            return contenido
        return json.dumps({
            "resultado_truncado": contenido[:limite],
            "aviso": "Resultado truncado para respetar el límite de contexto.",
        }, ensure_ascii=False)

    def chat(
        self,
        db: Session,
        mensaje: str,
        usuario,
    ) -> dict:
        usuario_id = usuario.id
        mensaje = mensaje.strip()
        if not mensaje:
            raise ValueError("El mensaje no puede estar vacío.")

        contexto, texto_contexto = self._texto_contexto(usuario_id)
        messages = [{
            "role": "system",
            "content": (
                MOTOR_AI_SYSTEM_PROMPT
                + "\n\nFECHA Y HORA ACTUAL DEL SISTEMA MOTORDesk: "
                + datetime.now().isoformat()
                + "\nUtiliza esta fecha para interpretar referencias temporales "
                "como hoy, mañana, ayer, esta semana, el próximo lunes o este mes."
                + "\n\nCONTEXTO ACTUAL DE LA CONVERSACIÓN:\n"
                + texto_contexto
            ),
        }]

        # Solo persistimos el diálogo humano. Los tool calls se mantienen en la
        # petición actual para el proveedor, nunca en la memoria del usuario.
        messages.extend(self._mensajes_memoria(contexto))
        messages.append({"role": "user", "content": mensaje})
        conversation_store.agregar_mensaje(usuario_id, "user", mensaje)

        herramientas_usadas: list[str] = []
        tools_usuario = filtrar_tools_usuario(
            db=db,
            usuario=usuario,
            tools=MOTOR_AI_TOOLS,
        )
        tools_usuario = self._seleccionar_tools(mensaje, tools_usuario)
        nombres_tools = [
            tool["function"]["name"]
            for tool in tools_usuario
        ]
        if nombres_tools:
            messages[0]["content"] += (
                "\n\nHERRAMIENTAS HABILITADAS PARA ESTA CONSULTA:\n- "
                + "\n- ".join(nombres_tools)
                + "\nSolo puedes invocar exactamente uno de esos nombres. "
                "No inventes herramientas ni SQL."
            )
        else:
            messages[0]["content"] += (
                "\n\nNo hay herramientas habilitadas para esta consulta. "
                "No generes llamadas de función; responde de forma conversacional "
                "o indica que el usuario no dispone del permiso necesario."
            )
        try:
            max_iteraciones = int(os.getenv("GROQ_MAX_TOOL_ITERATIONS", "4"))
        except ValueError:
            max_iteraciones = 4

        for _ in range(max(1, max_iteraciones)):
            try:
                response = self.provider.chat(
                    messages=messages,
                    tools=tools_usuario,
                )
            except AIProviderToolUseError:
                # Algunos modelos intentan generar una función alucinada aun
                # cuando no está en el catálogo filtrado. Reintentamos una vez
                # sin tools, sin convertir ese fallo del proveedor en un 502.
                fallback = messages + [{
                    "role": "system",
                    "content": (
                        "Responde ahora sin llamar ninguna herramienta. "
                        "No inventes datos: si la consulta requiere una herramienta, "
                        "explica de forma breve que no está disponible para esta petición."
                    ),
                }]
                try:
                    response = self.provider.chat(messages=fallback, tools=None)
                except AIProviderToolUseError:
                    respuesta_final = (
                        "No puedo consultar esa información en este momento. "
                        "Prueba a reformular la consulta o accede al módulo correspondiente."
                    )
                    conversation_store.agregar_mensaje(
                        usuario_id,
                        "assistant",
                        respuesta_final,
                    )
                    return {
                        "respuesta": respuesta_final,
                        "herramientas_usadas": herramientas_usadas,
                    }
            message = response.choices[0].message

            if not message.tool_calls:
                respuesta_final = (message.content or "").strip() or (
                    "No he podido generar una respuesta."
                )
                conversation_store.agregar_mensaje(
                    usuario_id, "assistant", respuesta_final
                )
                return {
                    "respuesta": respuesta_final,
                    "herramientas_usadas": herramientas_usadas,
                }

            assistant_message = {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [],
            }
            for tool_call in message.tool_calls:
                assistant_message["tool_calls"].append({
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                })
            messages.append(assistant_message)

            for tool_call in message.tool_calls:
                nombre = tool_call.function.name
                try:
                    argumentos = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    argumentos = {}

                try:
                    resultado = ejecutar_tool(
                        nombre=nombre,
                        argumentos=argumentos,
                        db=db,
                        usuario=usuario,
                    )
                    contexto_extraido = extraer_contexto(resultado)
                    if contexto_extraido:
                        conversation_store.actualizar_contexto(
                            usuario_id=usuario_id,
                            **contexto_extraido,
                        )
                except PermissionError as error:
                    resultado = {"error": str(error)}
                except Exception as error:
                    print(f"Error tool {nombre}:", repr(error))
                    resultado = {"error": "No se ha podido consultar esta información."}

                herramientas_usadas.append(nombre)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": self._contenido_tool(resultado),
                })

        respuesta_final = "No he podido completar la consulta correctamente."
        conversation_store.agregar_mensaje(usuario_id, "assistant", respuesta_final)
        return {
            "respuesta": respuesta_final,
            "herramientas_usadas": herramientas_usadas,
        }
