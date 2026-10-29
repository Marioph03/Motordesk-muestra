from sqlalchemy.orm import Session

from app.repositories.empresa_repository import EmpresaRepository
from app.schemas.empresa import (
    EmpresaCreate,
    EmpresaUpdate
)

import os
import shutil

from fastapi import UploadFile

from app.schemas.empresa import EmpresaResponse
from app.schemas.paginated_response import PaginatedResponse
from app.schemas.pagination import PaginationParams

class EmpresaService:

    @staticmethod
    def get_all(
        db: Session
    ):
        return EmpresaRepository.get_all(db)

    @staticmethod
    def get_by_id(
        db: Session,
        empresa_id: int
    ):

        empresa = EmpresaRepository.get_by_id(
            db,
            empresa_id
        )

        if empresa is None:
            raise ValueError(
                "Empresa no encontrada"
            )

        return empresa

    @staticmethod
    def create(
        db: Session,
        empresa: EmpresaCreate
    ):

        empresa_existente = (
            EmpresaRepository.get_by_nif(
                db,
                empresa.nif
            )
        )

        if empresa_existente:
            raise ValueError(
                "Ya existe una empresa con ese NIF"
            )

        return EmpresaRepository.create(
            db,
            empresa.model_dump()
        )

    @staticmethod
    def update(
        db: Session,
        empresa_id: int,
        datos: EmpresaUpdate
    ):

        empresa = EmpresaRepository.get_by_id(
            db,
            empresa_id
        )

        if empresa is None:
            raise ValueError(
                "Empresa no encontrada"
            )

        datos_actualizados = datos.model_dump(
            exclude_unset=True
        )

        if (
            "nif" in datos_actualizados
            and datos_actualizados["nif"] != empresa.nif
        ):

            empresa_existente = (
                EmpresaRepository.get_by_nif(
                    db,
                    datos_actualizados["nif"]
                )
            )

            if empresa_existente:
                raise ValueError(
                    "Ya existe una empresa con ese NIF"
                )

        return EmpresaRepository.update(
            db,
            empresa,
            datos_actualizados
        )

    @staticmethod
    def delete(
        db: Session,
        empresa_id: int
    ):

        empresa = EmpresaRepository.get_by_id(
            db,
            empresa_id
        )

        if empresa is None:
            raise ValueError(
                "Empresa no encontrada"
            )

        EmpresaRepository.delete(
            db,
            empresa
        )
        
    @staticmethod
    def subir_logo(
        db: Session,
        empresa_id: int,
        logo: UploadFile
    ):

        empresa = EmpresaRepository.get_by_id(
            db,
            empresa_id
        )

        if empresa is None:
            raise ValueError(
                "Empresa no encontrada"
            )

        extension = os.path.splitext(
            logo.filename
        )[1].lower()

        if extension not in [
            ".png",
            ".jpg",
            ".jpeg",
            ".webp"
        ]:
            raise ValueError(
                "Formato de imagen no válido"
            )

        nombre_archivo = (
            f"logo_empresa_{empresa.id}{extension}"
        )

        ruta = os.path.join(
            "uploads",
            "logos",
            nombre_archivo
        )

        with open(
            ruta,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                logo.file,
                buffer
            )

        empresa.logo = ruta.replace("\\", "/")

        db.commit()
        db.refresh(empresa)

        return empresa
    
    @staticmethod
    def get_paginated(
        db: Session,
        pagination: PaginationParams
    ):
        items, total = EmpresaRepository.get_paginated(
            db,
            pagination
        )

        return PaginatedResponse[EmpresaResponse].create(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size
        )
"""Mantenimiento de datos de empresa conservados por compatibilidad histórica."""
