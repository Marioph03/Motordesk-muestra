"""Servicio de vehículos y su asociación obligatoria con un cliente."""

from sqlalchemy.orm import Session

from app.repositories.vehiculo_repository import VehiculoRepository
from app.repositories.cliente_repository import ClienteRepository
from app.schemas.vehiculo import VehiculoCreate

from app.schemas.vehiculo import VehiculoResponse
from app.schemas.pagination import PaginationParams
from app.schemas.paginated_response import PaginatedResponse

class VehiculoService:

    @staticmethod
    def _normalizar_bastidor(bastidor: str | None) -> str | None:
        """Convierte un bastidor vacío en NULL para respetar su unicidad."""
        if bastidor is None:
            return None

        valor = bastidor.strip().upper()
        return valor or None

    @staticmethod
    def get_all(db: Session):
        return VehiculoRepository.get_all(db)

    @staticmethod
    def get_by_id(db: Session, vehiculo_id: int):
        vehiculo = VehiculoRepository.get_by_id(db, vehiculo_id)

        if vehiculo is None:
            raise ValueError("Vehículo no encontrado")

        return vehiculo

    @staticmethod
    def get_by_matricula(db: Session, matricula: str):
        return VehiculoRepository.get_by_matricula(db, matricula)

    @staticmethod
    def get_by_cliente(db: Session, cliente_id: int):
        return VehiculoRepository.get_by_cliente(db, cliente_id)

    @staticmethod
    def create(db: Session, vehiculo: VehiculoCreate):

        vehiculo.matricula = vehiculo.matricula.strip().upper()
        vehiculo.bastidor = VehiculoService._normalizar_bastidor(
            vehiculo.bastidor
        )

        cliente = ClienteRepository.get_by_id(
            db,
            vehiculo.cliente_id
        )

        if cliente is None:
            raise ValueError("El cliente no existe")

        existente = VehiculoRepository.get_by_matricula(
            db,
            vehiculo.matricula
        )

        if existente:
            raise ValueError("La matrícula ya existe")

        if vehiculo.bastidor:
            existente_bastidor = VehiculoRepository.get_by_bastidor(
                db,
                vehiculo.bastidor,
            )

            if existente_bastidor:
                raise ValueError("El bastidor ya existe")

        if (
            vehiculo.kilometros is not None
            and vehiculo.kilometros < 0
        ):
            raise ValueError(
                "Los kilómetros no pueden ser negativos."
            )

        return VehiculoRepository.create(
            db,
            vehiculo
        )
    
    @staticmethod
    def update(db: Session, vehiculo_id: int, datos: dict):

        vehiculo = VehiculoRepository.get_by_id(db, vehiculo_id)

        if vehiculo is None:
            raise ValueError("Vehículo no encontrado")

        # Si se modifica la matrícula, comprueba los duplicados
        existente = None

        if "matricula" in datos:

            datos["matricula"] = datos["matricula"].strip().upper()

            existente = VehiculoRepository.get_by_matricula(
                db,
                datos["matricula"]
        )

        if existente and existente.id != vehiculo_id:
            raise ValueError("La matrícula ya existe")

        if "bastidor" in datos:
            datos["bastidor"] = VehiculoService._normalizar_bastidor(
                datos["bastidor"]
            )

            if datos["bastidor"]:
                existente_bastidor = VehiculoRepository.get_by_bastidor(
                    db,
                    datos["bastidor"],
                )

                if (
                    existente_bastidor
                    and existente_bastidor.id != vehiculo_id
                ):
                    raise ValueError("El bastidor ya existe")

        if (
            "kilometros" in datos
            and datos["kilometros"] is not None
            and datos["kilometros"] < 0
        ):
            raise ValueError("Los kilómetros no pueden ser negativos")

        return VehiculoRepository.update(
            db,
            vehiculo,
            datos
        )
        
    @staticmethod
    def delete(db: Session, vehiculo_id: int):

        vehiculo = VehiculoRepository.get_by_id(
            db,
            vehiculo_id
        )

        if vehiculo is None:
            raise ValueError("Vehículo no encontrado")

        VehiculoRepository.delete(
            db,
            vehiculo
        )
        
    @staticmethod
    def search(db: Session, texto: str):
        return VehiculoRepository.search(db, texto.strip()) 
    
    @staticmethod
    def get_paginated(
    db: Session,
    pagination: PaginationParams,
    q: str | None = None
    ):
        items, total = VehiculoRepository.get_paginated(
        db,
        pagination,
        q
        )

        return PaginatedResponse[VehiculoResponse].create(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size
        )      
        
    @staticmethod
    def get_select(db: Session):
        return VehiculoRepository.get_select(db)
