"""Utilidades comunes de repositorio sin reglas de negocio."""

from sqlalchemy.orm import Query

from app.schemas.pagination import PaginationParams


class BaseRepository:
    """Centraliza paginación SQL para que todos los listados sean consistentes."""

    @staticmethod
    def paginate(
        query: Query,
        pagination: PaginationParams
    ):

        # El total se obtiene antes de offset/limit para construir paginación.

        total = query.count()

        items = (
            query
            .offset(pagination.offset)
            .limit(pagination.size)
            .all()
        )

        return items, total
