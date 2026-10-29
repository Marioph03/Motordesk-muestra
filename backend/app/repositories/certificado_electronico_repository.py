from sqlalchemy.orm import Session

from app.models.certificado_electronico import CertificadoElectronico


class CertificadoElectronicoRepository:

    @staticmethod
    def get_all(db: Session):
        return db.query(CertificadoElectronico).all()

    @staticmethod
    def get_by_empresa(
        db: Session,
        empresa_id: int
    ):
        return (
            db.query(CertificadoElectronico)
            .filter(
                CertificadoElectronico.empresa_id == empresa_id
            )
            .first()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        certificado_id: int
    ):
        return (
            db.query(CertificadoElectronico)
            .filter(
                CertificadoElectronico.id == certificado_id
            )
            .first()
        )

    @staticmethod
    def create(
        db: Session,
        datos: dict
    ):
        certificado = CertificadoElectronico(
            **datos
        )

        db.add(certificado)
        db.commit()
        db.refresh(certificado)

        return certificado

    @staticmethod
    def update(
        db: Session,
        certificado: CertificadoElectronico,
        datos: dict
    ):
        for campo, valor in datos.items():
            setattr(
                certificado,
                campo,
                valor
            )

        db.commit()
        db.refresh(certificado)

        return certificado

    @staticmethod
    def delete(
        db: Session,
        certificado: CertificadoElectronico
    ):
        db.delete(certificado)
        db.commit()
