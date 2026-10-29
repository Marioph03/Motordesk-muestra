from sqlalchemy.orm import Session

from app.models.registro_verifactu import (
    RegistroVerifactu
)


class RegistroVerifactuRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        registro_id: int
    ):

        return (
            db.query(RegistroVerifactu)
            .filter(
                RegistroVerifactu.id == registro_id
            )
            .first()
        )

    @staticmethod
    def get_by_factura(
        db: Session,
        factura_id: int
    ):

        return (
            db.query(RegistroVerifactu)
            .filter(
                RegistroVerifactu.factura_id == factura_id
            )
            .order_by(
                RegistroVerifactu.id.asc()
            )
            .all()
        )

    @staticmethod
    def get_ultimo(
        db: Session
    ):

        return (
            db.query(RegistroVerifactu)
            .order_by(
                RegistroVerifactu.id.desc()
            )
            .first()
        )

    @staticmethod
    def get_ultimo_aceptado(
        db: Session
    ):

        return (
            db.query(RegistroVerifactu)
            .filter(
                RegistroVerifactu.estado.in_([
                    "ACEPTADO",
                    "ACEPTADO_CON_ERRORES"
                ])
            )
            .order_by(
                RegistroVerifactu.id.desc()
            )
            .first()
        )

    @staticmethod
    def create(
        db: Session,
        datos: dict,
        commit: bool = True,
    ):

        registro = RegistroVerifactu(
            **datos
        )

        db.add(registro)
        if commit:
            db.commit()
            db.refresh(registro)
        else:
            db.flush()

        return registro

    @staticmethod
    def update_estado(
        db: Session,
        registro: RegistroVerifactu,
        datos: dict
    ):

        for key, value in datos.items():
            setattr(
                registro,
                key,
                value
            )

        db.commit()
        db.refresh(registro)

        return registro
"""Lectura y persistencia de la cadena de registros fiscales VERI*FACTU."""
