from datetime import datetime

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.actions.action_models import (
    AccionPendiente,
    EstadoAccion,
    TipoAccion,
)
from app.ai.actions.action_store import action_store
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.schemas.vehiculo import VehiculoCreate
from app.services.permisos_service import PermisosService
from app.services.vehiculo_service import VehiculoService


def _texto(datos: dict, campo: str) -> str | None:
    valor = datos.get(campo)
    if valor is None:
        return None
    return str(valor).strip() or None


def _normalizar_matricula(valor: str | None) -> str | None:
    if not valor:
        return None
    return valor.replace(" ", "").replace("-", "").upper()


def verificar_permiso_crear_vehiculo(
    db: Session,
    usuario_id: int,
) -> None:
    usuario = (
        db.query(Usuario)
        .filter(Usuario.id == usuario_id)
        .first()
    )

    if usuario is None or not usuario.activo:
        raise PermissionError(
            "El usuario no puede crear vehículos."
        )
    if not PermisosService.usuario_tiene_permiso(
        db,
        usuario,
        "vehiculos.crear",
    ):
        raise PermissionError(
            "No tienes permiso para crear vehículos."
        )


def validar_datos_vehiculo(
    db: Session,
    datos: dict,
) -> dict:
    cliente_id = datos.get("cliente_id")
    matricula = _normalizar_matricula(
        _texto(datos, "matricula")
    )
    marca = _texto(datos, "marca")
    modelo = _texto(datos, "modelo")
    version = _texto(datos, "version")
    bastidor = _texto(datos, "bastidor")
    color = _texto(datos, "color")
    combustible = _texto(datos, "combustible")

    if not cliente_id:
        raise ValueError("El vehículo necesita un cliente.")
    if not matricula:
        raise ValueError("El vehículo necesita una matrícula.")
    if not marca:
        raise ValueError("El vehículo necesita una marca.")
    if not modelo:
        raise ValueError("El vehículo necesita un modelo.")
    if len(matricula) > 10:
        raise ValueError("La matrícula es demasiado larga.")
    if len(marca) > 50 or len(modelo) > 50:
        raise ValueError("La marca o el modelo son demasiado largos.")

    cliente = (
        db.query(Cliente)
        .filter(Cliente.id == cliente_id)
        .first()
    )
    if cliente is None:
        raise ValueError(
            "El cliente seleccionado ya no existe."
        )

    existente = (
        db.query(Vehiculo)
        .filter(
            func.upper(
                func.replace(
                    func.replace(Vehiculo.matricula, " ", ""),
                    "-",
                    "",
                )
            ) == matricula
        )
        .first()
    )
    if existente:
        raise ValueError(
            f"Ya existe un vehículo con la matrícula {matricula}."
        )

    if bastidor:
        bastidor = bastidor.upper()
        existente_bastidor = (
            db.query(Vehiculo)
            .filter(func.upper(Vehiculo.bastidor) == bastidor)
            .first()
        )
        if existente_bastidor:
            raise ValueError(
                "Ya existe un vehículo con ese número de bastidor."
            )

    return {
        "cliente": cliente,
        "cliente_id": cliente.id,
        "matricula": matricula,
        "marca": marca,
        "modelo": modelo,
        "version": version,
        "bastidor": bastidor,
        "color": color,
        "combustible": combustible,
    }


def ejecutar_crear_vehiculo(
    db: Session,
    accion: AccionPendiente,
    usuario_id: int,
) -> dict:
    if accion.tipo != TipoAccion.CREAR_VEHICULO:
        raise ValueError("La acción no corresponde a un vehículo.")
    if accion.usuario_id != usuario_id:
        raise PermissionError("La acción pertenece a otro usuario.")
    if accion.estado != EstadoAccion.PENDIENTE:
        raise ValueError("La acción ya no está pendiente.")

    verificar_permiso_crear_vehiculo(db, usuario_id)
    datos = validar_datos_vehiculo(db, accion.datos)
    try:
        nuevo_vehiculo = VehiculoService.create(
            db,
            VehiculoCreate(
                cliente_id=datos["cliente_id"],
                matricula=datos["matricula"],
                marca=datos["marca"],
                modelo=datos["modelo"],
                version=datos["version"],
                bastidor=datos["bastidor"],
                color=datos["color"],
                combustible=datos["combustible"],
            ),
        )
    except IntegrityError as error:
        db.rollback()
        raise ValueError(
            "No se ha podido crear el vehículo porque la matrícula "
            "o el bastidor ya existe."
        ) from error

    ahora = datetime.utcnow().isoformat()
    accion.estado = EstadoAccion.EJECUTADA
    accion.confirmada_en = ahora
    accion.ejecutada_en = ahora
    accion.resultado = {
        "vehiculo_id": nuevo_vehiculo.id,
        "cliente_id": nuevo_vehiculo.cliente_id,
        "matricula": nuevo_vehiculo.matricula,
        "marca": nuevo_vehiculo.marca,
        "modelo": nuevo_vehiculo.modelo,
    }
    action_store.guardar(accion)

    return {
        "ok": True,
        "mensaje": (
            f"Vehículo {nuevo_vehiculo.matricula} creado correctamente."
        ),
        "vehiculo": accion.resultado,
    }
"""Propuesta y ejecución confirmada del alta de un vehículo mediante IA."""
