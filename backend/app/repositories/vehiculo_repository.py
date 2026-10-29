from sqlalchemy.orm import Session

from app.models.vehiculo import Vehiculo
from app.schemas.vehiculo import VehiculoCreate
from sqlalchemy import or_

from app.repositories.base_repository import BaseRepository
from app.schemas.pagination import PaginationParams


class VehiculoRepository:

    @staticmethod
    def get_all(db: Session):
        return db.query(Vehiculo).all()

    @staticmethod
    def get_by_id(db: Session, vehiculo_id: int):
        return db.query(Vehiculo).filter(
            Vehiculo.id == vehiculo_id
        ).first()

    @staticmethod
    def get_by_matricula(db: Session, matricula: str):
        return db.query(Vehiculo).filter(
            Vehiculo.matricula == matricula.upper()
        ).first()

    @staticmethod
    def get_by_bastidor(db: Session, bastidor: str):
        return db.query(Vehiculo).filter(
            Vehiculo.bastidor == bastidor
        ).first()

    @staticmethod
    def get_by_cliente(db: Session, cliente_id: int):
        return db.query(Vehiculo).filter(
            Vehiculo.cliente_id == cliente_id
        ).all()

    @staticmethod
    def create(db: Session, vehiculo: VehiculoCreate):

        nuevo = Vehiculo(
            cliente_id=vehiculo.cliente_id,
            matricula=vehiculo.matricula.strip().upper(),
            bastidor=vehiculo.bastidor,
            marca=vehiculo.marca,
            modelo=vehiculo.modelo,
            version=vehiculo.version,
            anio=vehiculo.anio,
            fecha_matriculacion=vehiculo.fecha_matriculacion,
            color=vehiculo.color,
            combustible=vehiculo.combustible,
            transmision=vehiculo.transmision,
            kilometros=vehiculo.kilometros,
            observaciones=vehiculo.observaciones
        )

        db.add(nuevo)
        db.flush()
        nuevo.codigo = f"VEH-{nuevo.id:06d}"
        db.commit()
        db.refresh(nuevo)

        return nuevo
    
    @staticmethod
    def update(db: Session, vehiculo_db: Vehiculo, datos: dict):

        for key, value in datos.items():
            setattr(vehiculo_db, key, value)

        db.commit()
        db.refresh(vehiculo_db)

        return vehiculo_db
    
    @staticmethod
    def delete(db: Session, vehiculo: Vehiculo):

        db.delete(vehiculo)

        db.commit()
            
    @staticmethod
    def search(db: Session, texto: str):
        return (
            db.query(Vehiculo)
            .filter(
                or_(
                    Vehiculo.codigo.ilike(f"%{texto}%"),
                    Vehiculo.matricula.ilike(f"%{texto}%"),
                    Vehiculo.marca.ilike(f"%{texto}%"),
                    Vehiculo.modelo.ilike(f"%{texto}%")
                )
            )
            .all()
        )
        
    @staticmethod
    def get_paginated(
        db: Session,
        pagination: PaginationParams,
        q: str | None = None
        ):
        
        query = (
            db.query(Vehiculo)
            .order_by(Vehiculo.matricula)
        )

        if q:
            texto = f"%{q}%"

            query = query.filter(
                or_(
                    Vehiculo.codigo.ilike(texto),
                    Vehiculo.matricula.ilike(texto),
                    Vehiculo.marca.ilike(texto),
                    Vehiculo.modelo.ilike(texto)
                )   
            )

        return BaseRepository.paginate(
            query,
            pagination
        )
        
    @staticmethod
    def get_select(db: Session):

        vehiculos = (
            db.query(Vehiculo)
            .order_by(Vehiculo.matricula)
            .all()
        )

        return [
            {
                "id": vehiculo.id,
                "cliente_id": vehiculo.cliente_id,
                "descripcion": (
                    f"{vehiculo.matricula} - "
                    f"{vehiculo.marca} {vehiculo.modelo}"
                )
            }
            for vehiculo in vehiculos
        ]
"""Consultas de vehículos, propietarios y búsquedas por identificación."""
