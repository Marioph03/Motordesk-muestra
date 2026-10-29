from typing import Any


def extraer_contexto(resultado: Any) -> dict:
    """Extrae identificadores de respuestas de tools sin interpretar texto."""
    if not isinstance(resultado, dict):
        return {}

    contexto: dict = {}
    for campo in (
        "cliente_id", "vehiculo_id", "orden_id", "factura_id", "cita_id", "matricula",
    ):
        valor = resultado.get(campo)
        if valor is not None:
            contexto[campo] = valor

    objetos = {
        "cliente": "cliente_id", "vehiculo": "vehiculo_id", "orden": "orden_id",
        "factura": "factura_id", "cita": "cita_id",
    }
    for clave, clave_id in objetos.items():
        objeto = resultado.get(clave)
        if not isinstance(objeto, dict):
            continue
        objeto_id = objeto.get("id") or objeto.get(clave_id)
        if objeto_id is not None:
            contexto[clave_id] = objeto_id
        if clave == "vehiculo":
            if objeto.get("matricula"):
                contexto["matricula"] = objeto["matricula"]
            if objeto.get("cliente_id") is not None:
                contexto["cliente_id"] = objeto["cliente_id"]
    return contexto
