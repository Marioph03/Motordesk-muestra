from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")


class PaginatedResponse(GenericModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        size: int
    ):
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=ceil(total / size) if total else 1
        )
"""Envoltorio común para respuestas API paginadas."""
