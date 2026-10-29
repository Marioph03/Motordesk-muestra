from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories.ausencia_personal_repository import (
    AusenciaPersonalRepository,
)
from app.repositories.cita_repository import CitaRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.ausencia_personal_service import AusenciaPersonalService


class PersonalService:
    @staticmethod
    def obtener_resumen_operativo(
        db: Session,
        usuario_id: int,
    ) -> dict:
        usuario = UsuarioRepository.get_by_id(db, usuario_id)
        if usuario is None:
            raise ValueError("Usuario no encontrado")

        ahora = datetime.now()
        citas = sorted(
            (
                cita for cita in usuario.citas_asignadas
                if cita.fecha_fin >= ahora
                and cita.estado not in {
                    "Cancelada",
                    "No presentado",
                    "Completada",
                }
            ),
            key=lambda cita: cita.fecha_inicio,
        )
        ordenes = sorted(
            (
                orden for orden in usuario.ordenes_asignadas
                if orden.estado not in {
                    "Cerrada",
                    "Facturada",
                    "Cancelada",
                }
            ),
            key=lambda orden: orden.fecha_entrada,
            reverse=True,
        )
        ausencias = sorted(
            (
                ausencia for ausencia in usuario.ausencias
                if ausencia.fecha_fin >= ahora
            ),
            key=lambda ausencia: ausencia.fecha_inicio,
        )

        return {
            "usuario_id": usuario.id,
            "citas": [
                {
                    "id": cita.id,
                    "fecha_inicio": cita.fecha_inicio,
                    "fecha_fin": cita.fecha_fin,
                    "motivo": cita.motivo,
                    "estado": cita.estado,
                    "vehiculo_descripcion": " ".join(
                        parte for parte in [
                            cita.vehiculo.marca,
                            cita.vehiculo.modelo,
                            f"· {cita.vehiculo.matricula}",
                        ] if parte
                    ),
                }
                for cita in citas
            ],
            "ordenes": [
                {
                    "id": orden.id,
                    "numero": orden.numero,
                    "tipo": orden.tipo,
                    "estado": orden.estado,
                    "descripcion_averia": orden.descripcion_averia,
                }
                for orden in ordenes
            ],
            "ausencias": [
                {
                    "id": ausencia.id,
                    "tipo": ausencia.tipo,
                    "fecha_inicio": ausencia.fecha_inicio,
                    "fecha_fin": ausencia.fecha_fin,
                    "observaciones": ausencia.observaciones,
                }
                for ausencia in ausencias
            ],
        }

    @staticmethod
    def obtener_planificacion(
        db: Session,
        fecha_inicio: datetime,
        fecha_fin: datetime,
    ) -> list[dict]:
        """Obtiene la carga semanal real de cada miembro activo del equipo."""

        AusenciaPersonalService.validar_intervalo(
            fecha_inicio,
            fecha_fin,
        )

        resultado = []
        for usuario in UsuarioRepository.get_all(db):
            if not usuario.activo:
                continue

            bloques = []
            for ausencia in AusenciaPersonalRepository.get_solapadas(
                db,
                usuario.id,
                fecha_inicio,
                fecha_fin,
            ):
                bloques.append({
                    "tipo": ausencia.tipo,
                    "inicio": ausencia.fecha_inicio,
                    "fin": ausencia.fecha_fin,
                    "referencia": ausencia.tipo.replace("_", " ").title(),
                    "id": ausencia.id,
                })

            for cita in CitaRepository.get_solapadas_usuario(
                db,
                usuario.id,
                fecha_inicio,
                fecha_fin,
            ):
                bloques.append({
                    "tipo": "CITA",
                    "inicio": cita.fecha_inicio,
                    "fin": cita.fecha_fin,
                    "referencia": f"Cita #{cita.id} · {cita.motivo}",
                    "id": cita.id,
                })

            # Las órdenes se incorporarán aquí cuando dispongan de una fecha
            # prevista de salida. La fecha_salida actual es real, no prevista.
            bloques.sort(key=lambda bloque: bloque["inicio"])
            resultado.append({
                "usuario_id": usuario.id,
                "nombre": usuario.nombre,
                "apellidos": usuario.apellidos,
                "rol": usuario.rol,
                "bloques": bloques,
            })

        return resultado
