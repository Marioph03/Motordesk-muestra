PERMISOS_BASE = [

    # CLIENTES
    (
        "clientes.ver",
        "Ver clientes",
        "clientes"
    ),
    (
        "clientes.crear",
        "Crear clientes",
        "clientes"
    ),
    (
        "clientes.editar",
        "Editar clientes",
        "clientes"
    ),

    # VEHÍCULOS
    (
        "vehiculos.ver",
        "Ver vehículos",
        "vehiculos"
    ),
    (
        "vehiculos.crear",
        "Crear vehículos",
        "vehiculos"
    ),
    (
        "vehiculos.editar",
        "Editar vehículos",
        "vehiculos"
    ),

    # AGENDA
    (
        "agenda.ver",
        "Ver agenda",
        "agenda"
    ),
    (
        "agenda.crear",
        "Crear citas",
        "agenda"
    ),
    (
        "agenda.editar",
        "Gestionar citas",
        "agenda"
    ),

    # ÓRDENES
    (
        "ordenes.ver",
        "Ver órdenes",
        "ordenes"
    ),
    (
        "ordenes.crear",
        "Crear órdenes",
        "ordenes"
    ),
    (
        "ordenes.editar",
        "Editar órdenes",
        "ordenes"
    ),
    (
        "ordenes.cerrar",
        "Cerrar órdenes",
        "ordenes"
    ),

    # FACTURAS
    (
        "facturas.ver",
        "Ver facturas",
        "facturas"
    ),
    (
        "facturas.emitir",
        "Emitir facturas",
        "facturas"
    ),
    (
        "facturas.anular",
        "Anular facturas",
        "facturas"
    ),

    # STOCK
    (
        "stock.ver",
        "Ver almacén",
        "stock"
    ),
    (
        "stock.editar",
        "Editar artículos",
        "stock"
    ),
    (
        "stock.ajustar",
        "Ajustar existencias",
        "stock"
    ),

    # COMPRAS
    (
        "compras.ver",
        "Ver compras",
        "compras"
    ),
    (
        "compras.crear",
        "Crear pedidos",
        "compras"
    ),
    (
        "compras.recibir",
        "Recibir mercancía",
        "compras"
    ),

    # PROVEEDORES
    (
        "proveedores.ver",
        "Ver proveedores",
        "proveedores"
    ),
    (
        "proveedores.editar",
        "Gestionar proveedores",
        "proveedores"
    ),

    # PERSONAL
    (
        "personal.ver",
        "Ver personal",
        "personal"
    ),
    (
        "personal.editar",
        "Gestionar personal",
        "personal"
    ),

    # PERMISOS
    (
        "permisos.gestionar",
        "Gestionar roles y permisos",
        "permisos"
    ),

    # INFORMES
    (
        "informes.ver",
        "Ver informes",
        "informes"
    ),
]

from sqlalchemy.orm import Session

from app.models.permiso import Permiso
from app.models.rol import Rol

from app.repositories.permiso_repository import (
    PermisoRepository
)

from app.repositories.rol_repository import (
    RolRepository
)


def seed_permisos(
    db: Session
):

    for codigo, nombre, modulo in PERMISOS_BASE:

        existente = (
            PermisoRepository.get_by_codigo(
                db,
                codigo
            )
        )

        if existente:
            continue

        PermisoRepository.create(
            db,
            {
                "codigo":
                    codigo,

                "nombre":
                    nombre,

                "modulo":
                    modulo
            }
        )

    db.flush()

    permisos = (
        PermisoRepository.get_all(
            db
        )
    )


    # ADMIN
    admin = (
        RolRepository.get_by_nombre(
            db,
            "ADMIN"
        )
    )

    if admin is None:

        admin = RolRepository.create(
            db,
            {
                "nombre":
                    "ADMIN",

                "descripcion":
                    "Acceso completo",

                "activo":
                    True
            }
        )

    admin.permisos = permisos


    # RECEPCIÓN
    recepcion_codigos = {
        "clientes.ver",
        "clientes.crear",
        "clientes.editar",
        "vehiculos.ver",
        "vehiculos.crear",
        "vehiculos.editar",
        "agenda.ver",
        "agenda.crear",
        "agenda.editar",
        "ordenes.ver",
        "ordenes.crear",
        "ordenes.editar",
        "facturas.ver",
        "informes.ver"
    }

    _crear_o_actualizar_rol(
        db,
        "RECEPCION",
        "Personal de recepción",
        permisos,
        recepcion_codigos
    )


    # MECÁNICO
    mecanico_codigos = {
        "agenda.ver",
        "ordenes.ver",
        "ordenes.editar",
        "stock.ver"
    }

    _crear_o_actualizar_rol(
        db,
        "MECANICO",
        "Personal de taller",
        permisos,
        mecanico_codigos
    )


    # ALMACÉN
    almacen_codigos = {
        "stock.ver",
        "stock.editar",
        "stock.ajustar",
        "compras.ver",
        "compras.crear",
        "compras.recibir",
        "proveedores.ver",
        "proveedores.editar"
    }

    _crear_o_actualizar_rol(
        db,
        "ALMACEN",
        "Gestión de almacén y compras",
        permisos,
        almacen_codigos
    )

    db.commit()
    
def _crear_o_actualizar_rol(
    db: Session,
    nombre: str,
    descripcion: str,
    permisos,
    codigos: set[str]
):

    rol = (
        RolRepository.get_by_nombre(
            db,
            nombre
        )
    )

    if rol is None:

        rol = RolRepository.create(
            db,
            {
                "nombre":
                    nombre,

                "descripcion":
                    descripcion,

                "activo":
                    True
            }
        )

    rol.permisos = [
        permiso
        for permiso in permisos
        if permiso.codigo in codigos
    ]
"""Datos iniciales idempotentes de permisos y roles predeterminados."""
