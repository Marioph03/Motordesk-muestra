"""Configuracion inicial segura de una instalacion nueva de MotorDesk."""

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.configuracion_facturacion import ConfiguracionFacturacion
from app.models.configuracion_taller import ConfiguracionTaller
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.schemas.bootstrap import BootstrapInicialRequest


class BootstrapService:
    """Centraliza la primera configuracion de una instalacion."""

    @staticmethod
    def necesita_configuracion(db: Session) -> bool:
        """Indica si MotorDesk todavia necesita empresa y administrador."""
        existe_empresa = db.query(Empresa.id).first() is not None
        existe_usuario = db.query(Usuario.id).first() is not None

        return not (existe_empresa and existe_usuario)

    @staticmethod
    def inicializar(
        db: Session,
        datos: BootstrapInicialRequest,
    ) -> dict:
        """Crea empresa, configuraciones y administrador en una transaccion.

        Se crean modelos directamente, sin llamar a servicios que puedan
        confirmar cambios por separado. La instalacion queda completa o no
        queda escrita ningun registro si cualquier paso falla.
        """
        if not BootstrapService.necesita_configuracion(db):
            raise ValueError("MotorDesk ya ha sido configurado.")

        if db.query(Empresa.id).first() is not None:
            raise ValueError("Ya existe una empresa en esta instalacion.")

        if db.query(Usuario.id).first() is not None:
            raise ValueError("Ya existe un usuario en esta instalacion.")

        try:
            empresa = Empresa(
                nombre=datos.nombre_empresa.strip(),
                nombre_comercial=datos.nombre_comercial.strip(),
                nif=datos.nif.strip().upper(),
                direccion=datos.direccion.strip(),
                codigo_postal=datos.codigo_postal.strip(),
                ciudad=datos.ciudad.strip(),
                provincia=datos.provincia.strip(),
                telefono=datos.telefono.strip(),
                email=str(datos.email_empresa).strip().lower(),
                iva_defecto=datos.iva_defecto,
                regimen_fiscal=datos.regimen_fiscal,
                moneda="EUR",
                color_primario="#1F3D72",
                color_secundario="#6C757D",
            )
            db.add(empresa)
            db.flush()

            configuracion_taller = ConfiguracionTaller(
                nombre_comercial=datos.nombre_comercial.strip(),
                razon_social=datos.nombre_empresa.strip(),
                nif_cif=datos.nif.strip().upper(),
                telefono=datos.telefono.strip(),
                email=str(datos.email_empresa).strip().lower(),
                direccion=datos.direccion.strip(),
                codigo_postal=datos.codigo_postal.strip(),
                localidad=datos.ciudad.strip(),
                provincia=datos.provincia.strip(),
                pais="Espana",
            )
            db.add(configuracion_taller)

            configuracion_facturacion = ConfiguracionFacturacion(
                modo_facturacion="PRUEBAS",
                serie_pruebas=datos.serie_pruebas,
                serie_facturas=datos.serie_facturas,
                permitir_envio_aeat=False,
            )
            db.add(configuracion_facturacion)

            password_hash = get_password_hash(datos.password_admin)

            # Una instalación no puede confirmarse con una contraseña que el
            # propio backend no sea capaz de verificar inmediatamente.
            if not verify_password(datos.password_admin, password_hash):
                raise RuntimeError(
                    "No se ha podido preparar la contraseña del administrador."
                )

            administrador = Usuario(
                nombre=datos.nombre_admin.strip(),
                apellidos=datos.apellidos_admin.strip(),
                email=str(datos.email_admin).strip().lower(),
                password_hash=password_hash,
                rol="ADMIN",
                activo=True,
                empresa_id=empresa.id,
            )
            db.add(administrador)

            db.commit()

            db.refresh(empresa)
            db.refresh(administrador)
            db.refresh(configuracion_taller)
            db.refresh(configuracion_facturacion)

            return {
                "configurado": True,
                "empresa_id": empresa.id,
                "usuario_id": administrador.id,
                "mensaje": "MotorDesk se ha configurado correctamente.",
            }

        except Exception:
            db.rollback()
            raise
