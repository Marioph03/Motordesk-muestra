"""Administración de roles y resolución de permisos efectivos de usuarios."""

from sqlalchemy.orm import Session

from app.repositories.permiso_repository import (
    PermisoRepository
)

from app.repositories.rol_repository import (
    RolRepository
)
from app.core.roles import normalizar_nombre_rol

from app.schemas.rol import (
    RolCreate,
    RolUpdate
)


class PermisosService:

    @staticmethod
    def listar_permisos(
        db: Session
    ):

        return (
            PermisoRepository.get_all(
                db
            )
        )


    @staticmethod
    def listar_roles(
        db: Session
    ):

        return (
            RolRepository.get_all(
                db
            )
        )


    @staticmethod
    def obtener_rol(
        db: Session,
        rol_id: int
    ):

        rol = (
            RolRepository.get_by_id(
                db,
                rol_id
            )
        )

        if rol is None:

            raise ValueError(
                "Rol no encontrado"
            )

        return rol


    @staticmethod
    def crear_rol(
        db: Session,
        datos: RolCreate
    ):

        nombre = (
            datos.nombre
            .strip()
            .upper()
        )

        if not nombre:

            raise ValueError(
                "El nombre del rol es obligatorio"
            )

        existente = (
            RolRepository.get_by_nombre(
                db,
                nombre
            )
        )

        if existente:

            raise ValueError(
                "Ya existe un rol con ese nombre"
            )

        permisos = (
            PermisosService
            ._obtener_permisos(
                db,
                datos.permisos_ids
            )
        )

        try:

            rol = (
                RolRepository.create(
                    db,
                    {
                        "nombre":
                            nombre,

                        "descripcion":
                            datos.descripcion,

                        "activo":
                            datos.activo
                    }
                )
            )

            rol.permisos = permisos

            db.commit()

            return (
                RolRepository.get_by_id(
                    db,
                    rol.id
                )
            )

        except Exception:

            db.rollback()
            raise


    @staticmethod
    def actualizar_rol(
        db: Session,
        rol_id: int,
        datos: RolUpdate
    ):

        rol = (
            PermisosService.obtener_rol(
                db,
                rol_id
            )
        )

        cambios = datos.model_dump(
            exclude_unset=True
        )

        permisos_ids = cambios.pop(
            "permisos_ids",
            None
        )

        if rol.nombre == "ADMIN":

            if cambios.get("activo") is False:
                raise ValueError(
                    "El rol ADMIN no se puede desactivar"
                )

            if permisos_ids is not None and not permisos_ids:
                raise ValueError(
                    "El rol ADMIN no puede quedarse "
                    "sin permisos"
                )

            if (
                "nombre" in cambios
                and (cambios["nombre"] or "").strip().upper()
                    != "ADMIN"
            ):
                raise ValueError(
                    "El rol ADMIN no se puede renombrar"
                )

        if "nombre" in cambios:

            nombre = (
                cambios["nombre"]
                or ""
            ).strip().upper()

            if not nombre:

                raise ValueError(
                    "El nombre del rol "
                    "no puede estar vacío"
                )

            existente = (
                RolRepository.get_by_nombre(
                    db,
                    nombre
                )
            )

            if (
                existente
                and existente.id != rol.id
            ):

                raise ValueError(
                    "Ya existe otro rol "
                    "con ese nombre"
                )

            cambios["nombre"] = nombre

        try:

            RolRepository.update(
                db,
                rol,
                cambios
            )

            if permisos_ids is not None:

                rol.permisos = (
                    PermisosService
                    ._obtener_permisos(
                        db,
                        permisos_ids
                    )
                )

            db.commit()

            return (
                RolRepository.get_by_id(
                    db,
                    rol.id
                )
            )

        except Exception:

            db.rollback()
            raise


    @staticmethod
    def usuario_tiene_permiso(
        db: Session,
        usuario,
        codigo_permiso: str
    ) -> bool:

        # El administrador siempre conserva el acceso durante la transición
        # desde los roles heredados (por ejemplo, "Administrador") hacia
        # roles configurables por permisos.
        if normalizar_nombre_rol(usuario.rol) == "ADMIN":
            return True

        # Compatibilidad temporal con Usuario.rol
        rol = (
            RolRepository.get_by_nombre(
                db,
                normalizar_nombre_rol(usuario.rol)
            )
        )

        if rol is None:
            return False

        if not rol.activo:
            return False

        return any(
            permiso.codigo == codigo_permiso
            for permiso in rol.permisos
        )


    @staticmethod
    def obtener_codigos_usuario(
        db: Session,
        usuario,
    ) -> list[str]:

        if normalizar_nombre_rol(usuario.rol) == "ADMIN":
            return [
                permiso.codigo
                for permiso in PermisoRepository.get_all(db)
            ]

        rol = RolRepository.get_by_nombre(
            db,
            normalizar_nombre_rol(usuario.rol),
        )

        if rol is None or not rol.activo:
            return []

        return sorted(
            permiso.codigo
            for permiso in rol.permisos
        )


    @staticmethod
    def _obtener_permisos(
        db: Session,
        permisos_ids: list[int]
    ):

        permisos = []

        for permiso_id in permisos_ids:

            permiso = (
                PermisoRepository.get_by_id(
                    db,
                    permiso_id
                )
            )

            if permiso is None:

                raise ValueError(
                    f"Permiso {permiso_id} "
                    f"no encontrado"
                )

            permisos.append(
                permiso
            )

        return permisos
