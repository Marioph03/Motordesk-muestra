"""Prueba funcional persistente del módulo Personal.

Los registros QA se conservan deliberadamente para poder revisarlos en la UI.
"""
from datetime import datetime, timedelta
import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.database.database import SessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.cita import Cita
from app.models.orden_reparacion import OrdenReparacion
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.repositories.cita_repository import CitaRepository
from app.schemas.ausencia_personal import AusenciaPersonalCreate
from app.schemas.cita import CitaCreate, CitaUpdate
from app.schemas.orden_reparacion import OrdenReparacionCreate, OrdenReparacionUpdate
from app.schemas.rol import RolUpdate
from app.services.ausencia_personal_service import AusenciaPersonalService
from app.services.cita_service import CitaService
from app.services.orden_reparacion_service import OrdenReparacionService
from app.services.permisos_service import PermisosService
from app.services.personal_service import PersonalService


PREFIJO = "QA Personal 2026"
ROL_QA = "QA_SIN_PERMISOS_20260821"
EMAIL_QA_LIBRE = "qa.personal.libre@talleresfaustinoprada.com"
EMAIL_QA_AUSENTE = "qa.personal.ausente@talleresfaustinoprada.com"


def esperar_error(accion, texto):
    try:
        accion()
    except ValueError as error:
        if texto not in str(error):
            raise AssertionError(f"Error inesperado: {error!s}")
        return str(error)
    raise AssertionError("La operación debía fallar")


def crear_o_recuperar_usuario(db, email, nombre, apellidos):
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None:
        usuario = Usuario(
            nombre=nombre,
            apellidos=apellidos,
            email=email,
            password_hash=get_password_hash("QaPersonal2026!"),
            rol=ROL_QA,
            activo=True,
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    return usuario


def buscar_huecos(db):
    inicio_base = (datetime.now() + timedelta(days=1)).replace(
        hour=8, minute=0, second=0, microsecond=0
    )
    huecos = []
    for dia in range(7):
        for hora in range(8, 19):
            inicio = inicio_base + timedelta(days=dia, hours=hora - 8)
            fin = inicio + timedelta(minutes=15)
            if not CitaRepository.get_solapadas(db, inicio, fin):
                huecos.append((inicio, fin))
                if len(huecos) == 2:
                    return huecos
    raise AssertionError("No se encontraron dos huecos de prueba para citas")


def main():
    db = SessionLocal()
    try:
        # Corrige los correos .local creados por la primera ejecución de QA.
        # EmailStr no admite dominios reservados al serializar /usuarios/.
        correos_anteriores = {
            "qa.personal.libre@motordesk.local": EMAIL_QA_LIBRE,
            "qa.personal.ausente@motordesk.local": EMAIL_QA_AUSENTE,
        }
        for anterior, nuevo in correos_anteriores.items():
            usuario_legacy = db.query(Usuario).filter(Usuario.email == anterior).first()
            if usuario_legacy is not None:
                usuario_legacy.email = nuevo
        db.commit()

        rol = db.query(Rol).filter(Rol.nombre == ROL_QA).first()
        if rol is None:
            rol = Rol(nombre=ROL_QA, descripcion="Rol QA sin permisos", activo=True)
            db.add(rol)
            db.commit()

        libre = crear_o_recuperar_usuario(
            db, EMAIL_QA_LIBRE, "QA Disponible", "Personal 2026"
        )
        ausente = crear_o_recuperar_usuario(
            db, EMAIL_QA_AUSENTE, "QA Ausente", "Personal 2026"
        )
        vehiculo = db.query(Vehiculo).first()
        if vehiculo is None:
            raise AssertionError("No hay vehículo existente para crear las citas QA")

        ahora = datetime.now()
        ausencia = next(
            (item for item in ausente.ausencias if item.observaciones == f"{PREFIJO} · Vacaciones de prueba"),
            None,
        )
        if ausencia is None:
            ausencia = AusenciaPersonalService.create(
                db,
                AusenciaPersonalCreate(
                    usuario_id=ausente.id,
                    tipo="VACACIONES",
                    fecha_inicio=ahora - timedelta(hours=1),
                    fecha_fin=ahora + timedelta(days=3),
                    observaciones=f"{PREFIJO} · Vacaciones de prueba",
                ),
            )

        hueco_cita, hueco_error = buscar_huecos(db)
        cita = db.query(Cita).filter(Cita.motivo == f"{PREFIJO} · Cita asignada").first()
        if cita is None:
            cita = CitaService.create(
                db,
                CitaCreate(
                    cliente_id=vehiculo.cliente_id,
                    vehiculo_id=vehiculo.id,
                    usuarios_ids=[libre.id],
                    fecha_inicio=hueco_cita[0],
                    fecha_fin=hueco_cita[1],
                    motivo=f"{PREFIJO} · Cita asignada",
                ),
            )

        error_cita_creacion = esperar_error(
            lambda: CitaService.create(
                db,
                CitaCreate(
                    cliente_id=vehiculo.cliente_id,
                    vehiculo_id=vehiculo.id,
                    usuarios_ids=[ausente.id],
                    fecha_inicio=hueco_error[0],
                    fecha_fin=hueco_error[1],
                    motivo=f"{PREFIJO} · Cita bloqueada",
                ),
            ),
            "no está disponible",
        )
        error_cita_edicion = esperar_error(
            lambda: CitaService.update(
                db,
                cita.id,
                CitaUpdate(usuarios_ids=[ausente.id]),
            ),
            "no está disponible",
        )

        orden = db.query(OrdenReparacion).filter(
            OrdenReparacion.descripcion_averia == f"{PREFIJO} · Orden asignada"
        ).first()
        if orden is None:
            orden = OrdenReparacionService.create(
                db,
                OrdenReparacionCreate(
                    tipo="OR",
                    vehiculo_id=vehiculo.id,
                    descripcion_averia=f"{PREFIJO} · Orden asignada",
                    garantia=False,
                    usuarios_ids=[libre.id],
                ),
            )
        error_orden_edicion = esperar_error(
            lambda: OrdenReparacionService.update(
                db,
                orden.id,
                OrdenReparacionUpdate(usuarios_ids=[ausente.id]),
            ),
            "no está disponible",
        )

        admin = db.query(Usuario).filter(Usuario.rol.in_(["ADMIN", "Administrador"])).first()
        admin_proteccion = "SIN_ADMIN"
        if admin is not None:
            admin_rol = db.query(Rol).filter(Rol.nombre == "ADMIN").first()
            if admin_rol is not None:
                admin_proteccion = esperar_error(
                    lambda: PermisosService.actualizar_rol(
                        db, admin_rol.id, RolUpdate(activo=False)
                    ),
                    "no se puede desactivar",
                )

        token_qa = create_access_token({"sub": ausente.email})
        consulta = urlencode({
            "fecha_inicio": ahora.isoformat(),
            "fecha_fin": (ahora + timedelta(hours=1)).isoformat(),
        })
        solicitud = Request(
            f"http://127.0.0.1:8000/personal/disponibilidad?{consulta}",
            headers={"Authorization": f"Bearer {token_qa}"},
        )
        try:
            urlopen(solicitud, timeout=10)
            raise AssertionError("Se esperaba 403 y la petición fue aceptada")
        except HTTPError as error:
            respuesta_403 = error.code
        if respuesta_403 != 403:
            raise AssertionError(f"Se esperaba 403, recibido {respuesta_403}")

        respuesta_200 = None
        if admin is not None:
            token_admin = create_access_token({"sub": admin.email})
            solicitud_admin = Request(
                f"http://127.0.0.1:8000/personal/disponibilidad?{consulta}",
                headers={"Authorization": f"Bearer {token_admin}"},
            )
            with urlopen(solicitud_admin, timeout=10) as respuesta:
                respuesta_200 = respuesta.status
            if respuesta_200 != 200:
                raise AssertionError(f"Se esperaba 200, recibido {respuesta_200}")

        planificacion = PersonalService.obtener_planificacion(
            db,
            ahora - timedelta(days=1),
            ahora + timedelta(days=4),
        )
        bloque_ausencia = any(
            bloque["id"] == ausencia.id
            for usuario in planificacion
            for bloque in usuario["bloques"]
        )
        bloque_cita = any(
            bloque["id"] == cita.id and bloque["tipo"] == "CITA"
            for usuario in planificacion
            for bloque in usuario["bloques"]
        )
        if not bloque_ausencia or not bloque_cita:
            raise AssertionError("La planificación no contiene los bloques QA esperados")

        resumen = PersonalService.obtener_resumen_operativo(db, libre.id)
        if cita.id not in [item["id"] for item in resumen["citas"]]:
            raise AssertionError("El resumen operativo no contiene la cita QA")
        if orden.id not in [item["id"] for item in resumen["ordenes"]]:
            raise AssertionError("El resumen operativo no contiene la orden QA")

        print(json.dumps({
            "resultado": "OK",
            "rol_qa": ROL_QA,
            "usuarios": {"disponible_id": libre.id, "ausente_id": ausente.id},
            "ausencia_id": ausencia.id,
            "cita_id": cita.id,
            "orden_id": orden.id,
            "errores_esperados": {
                "cita_crear": error_cita_creacion,
                "cita_editar": error_cita_edicion,
                "orden_editar": error_orden_edicion,
                "admin": admin_proteccion,
                "http_403": respuesta_403,
                "http_200_admin": respuesta_200,
            },
            "planificacion": {"ausencia": bloque_ausencia, "cita": bloque_cita},
            "resumen_operativo": True,
        }, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
