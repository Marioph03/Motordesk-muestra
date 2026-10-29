"""Reglas de negocio de clientes entre los endpoints y el repositorio."""

from sqlalchemy.orm import Session

from app.repositories.cliente_repository import ClienteRepository
from app.schemas.cliente import ClienteCreate

from app.schemas.cliente import ClienteResponse
from app.schemas.paginated_response import PaginatedResponse
from app.schemas.pagination import PaginationParams

class ClienteService:
    """Frontera para validaciones de clientes que superen al repositorio."""

    @staticmethod
    def get_all(db: Session):
        return ClienteRepository.get_all(db)

    @staticmethod
    def get_by_id(db: Session, cliente_id: int):
        return ClienteRepository.get_by_id(db, cliente_id)

    @staticmethod
    def create(
    db: Session,
    cliente: ClienteCreate,
    current_user
    ):
        return ClienteRepository.create(
            db,
            cliente,
            current_user
        )
    
    @staticmethod
    def update(db: Session, cliente_id: int, cliente):
        return ClienteRepository.update(
            db,
            cliente_id,
            cliente
        )

    @staticmethod
    def desactivar(db: Session, cliente_id: int):
        return ClienteRepository.desactivar(
            db,
            cliente_id
        )
        
    @staticmethod
    def buscar(db: Session, texto: str):
        return ClienteRepository.buscar(db, texto)
    
    @staticmethod
    def get_paginated(
        db: Session,
        pagination: PaginationParams,
        q: str | None = None
    ):
        items, total = ClienteRepository.get_paginated(
            db,
            pagination,
            q
        )

        return PaginatedResponse[ClienteResponse].create(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size
        )
        
    @staticmethod
    def delete(
        db: Session,
        cliente_id: int
    ):
        return ClienteRepository.delete(
            db,
            cliente_id
        )
        
    @staticmethod
    def get_select(db: Session):
        return ClienteRepository.get_select(db)
