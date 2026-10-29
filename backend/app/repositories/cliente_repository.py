from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.cliente import Cliente
from app.models.vehiculo import Vehiculo
from app.schemas.cliente import ClienteCreate
from sqlalchemy import or_

from app.repositories.base_repository import BaseRepository
from app.schemas.pagination import PaginationParams


class ClienteRepository:

    @staticmethod
    def get_all(db: Session):
        return db.query(Cliente).all()

    @staticmethod
    def get_by_id(db: Session, cliente_id: int):
        return db.query(Cliente).filter(
            Cliente.id == cliente_id
        ).first()

    @staticmethod
    def create(
        db: Session,
        cliente: ClienteCreate,
        current_user
    ):

        nuevo_cliente = Cliente(
            nombre=cliente.nombre,
            apellidos=cliente.apellidos,
            dni=cliente.dni,
            telefono=cliente.telefono,
            email=cliente.email,
            direccion=cliente.direccion,
            ciudad=cliente.ciudad,
            provincia=cliente.provincia,
            codigo_postal=cliente.codigo_postal,
            observaciones=cliente.observaciones
    )

        db.add(nuevo_cliente)
        # El identificador comercial depende de la clave que asigna la base de
        # datos, por eso se reserva primero y se completa antes del commit.
        db.flush()
        nuevo_cliente.codigo = f"CL-{nuevo_cliente.id:06d}"
        db.commit()

        db.refresh(nuevo_cliente)

        return nuevo_cliente
    
    @staticmethod
    def update(db: Session, cliente_id: int, datos):

        cliente = db.query(Cliente).filter(
            Cliente.id == cliente_id
        ).first()

        if not cliente:
            return None

        for campo, valor in datos.model_dump(exclude_unset=True).items():
            setattr(cliente, campo, valor)

        db.commit()
        db.refresh(cliente)

        return cliente
    
    @staticmethod
    def desactivar(db: Session, cliente_id: int):

        cliente = db.query(Cliente).filter(
            Cliente.id == cliente_id
        ).first()

        if cliente is None:
            return None

        cliente.activo = False

        db.commit()
        db.refresh(cliente)

        return cliente
    
    @staticmethod
    def buscar(db: Session, texto: str):
        return db.query(Cliente).filter(
            or_(
                Cliente.nombre.ilike(f"%{texto}%"),
                Cliente.codigo.ilike(f"%{texto}%"),
                Cliente.apellidos.ilike(f"%{texto}%"),
                Cliente.telefono.ilike(f"%{texto}%"),
                Cliente.email.ilike(f"%{texto}%"),
                Cliente.dni.ilike(f"%{texto}%"),
                Cliente.ciudad.ilike(f"%{texto}%"),
                Cliente.provincia.ilike(f"%{texto}%")
            )
        ).all()
        
    @staticmethod
    def get_paginated(
        db: Session,
        pagination: PaginationParams,
        q: str | None = None
    ):
        query = (
            db.query(Cliente)
            .outerjoin(Vehiculo, Vehiculo.cliente_id == Cliente.id)
            .order_by(Cliente.nombre)
        )

        if q:

            texto = f"%{q}%"

            query = query.filter(
                or_(
                    Cliente.nombre.ilike(texto),
                    Cliente.codigo.ilike(texto),
                    Cliente.apellidos.ilike(texto),
                    Cliente.dni.ilike(texto),
                    Cliente.telefono.ilike(texto),
                    Cliente.email.ilike(texto),
                    Cliente.ciudad.ilike(texto),
                    Cliente.provincia.ilike(texto),
                    Vehiculo.matricula.ilike(texto)
                )
            ).distinct()

        return BaseRepository.paginate(
            query,
            pagination
        )
        
    @staticmethod
    def get_select(db: Session):

        return (
            db.query(Cliente)
            .filter(Cliente.activo == True)
            .order_by(Cliente.nombre)
            .all()
        )
        
    @staticmethod
    def delete(
        db: Session,
        cliente_id: int
    ):

        cliente = (
            db.query(Cliente)
            .filter(Cliente.id == cliente_id)
            .first()
        )

        if cliente is None:
            return False

        try:
            db.delete(cliente)
            db.commit()
        except IntegrityError as error:
            db.rollback()
            raise ValueError(
                "No se puede eliminar un cliente con documentos asociados. Usa Restablecer datos para borrar las pruebas."
            ) from error

        return True
"""Acceso a datos de clientes y búsquedas paginadas del taller."""
