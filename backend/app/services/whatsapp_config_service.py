from sqlalchemy.orm import Session

from app.models.configuracion_whatsapp import ConfiguracionWhatsApp
from app.models.empresa import Empresa
from app.services.secretos_service import SecretosService


class WhatsAppConfigService:

    @staticmethod
    def obtener(
        db: Session,
        empresa_id: int,
    ) -> ConfiguracionWhatsApp | None:
        """
        Obtiene la configuración de WhatsApp de una empresa.
        """
        return (
            db.query(ConfiguracionWhatsApp)
            .filter(ConfiguracionWhatsApp.empresa_id == empresa_id)
            .first()
        )

    @classmethod
    def guardar(
        cls,
        db: Session,
        empresa_id: int,
        whatsapp_business_account_id: str,
        phone_number_id: str,
        numero_whatsapp: str | None,
        access_token: str | None = None,
        activo: bool = True,
    ) -> ConfiguracionWhatsApp:
        """
        Crea o actualiza la configuración de WhatsApp.

        El access token se cifra antes de almacenarse.
        Si se está actualizando y no se proporciona un nuevo token,
        se conserva el existente.
        """

        config = cls.obtener(db, empresa_id)

        if config is None:
            if not access_token:
                raise ValueError(
                    "El access token es obligatorio al configurar WhatsApp por primera vez."
                )

            config = ConfiguracionWhatsApp(
                empresa_id=empresa_id,
            )

            db.add(config)

        config.whatsapp_business_account_id = (
            whatsapp_business_account_id
        )
        config.phone_number_id = phone_number_id
        config.numero_whatsapp = numero_whatsapp
        config.activo = activo

        if access_token:
            config.access_token_cifrado = SecretosService.cifrar(
                access_token
            )

        db.commit()
        db.refresh(config)

        return config

    @classmethod
    def obtener_token(
        cls,
        db: Session,
        empresa_id: int,
    ) -> str:
        """
        Devuelve el access token descifrado únicamente cuando
        el backend necesita comunicarse con Meta.
        """

        config = cls.obtener(db, empresa_id)

        if config is None:
            raise ValueError(
                "WhatsApp no está configurado para esta empresa."
            )

        if not config.activo:
            raise ValueError(
                "La integración de WhatsApp está desactivada."
            )

        if not config.access_token_cifrado:
            raise ValueError(
                "La configuración de WhatsApp no tiene access token."
            )

        return SecretosService.descifrar(
            config.access_token_cifrado
        )

    @classmethod
    def esta_configurado(
        cls,
        db: Session,
        empresa_id: int,
    ) -> bool:
        config = cls.obtener(db, empresa_id)

        if config is None:
            return False

        return bool(
            config.activo
            and config.whatsapp_business_account_id
            and config.phone_number_id
            and config.access_token_cifrado
        )

    @classmethod
    def migrar_desde_empresa(
        cls,
        db: Session,
        empresa_id: int,
    ) -> ConfiguracionWhatsApp:
        """Copia una configuración WhatsApp heredada sin modificar su origen.

        El token legado se cifra al guardarse en la tabla nueva. Los campos
        ``Empresa.whatsapp_*`` se conservan intactos para permitir una
        transición reversible de los envíos ya existentes.
        """
        empresa = (
            db.query(Empresa)
            .filter(Empresa.id == empresa_id)
            .first()
        )

        if empresa is None:
            raise ValueError("La empresa no existe.")

        if cls.obtener(db, empresa_id) is not None:
            raise ValueError(
                "La empresa ya tiene una configuración WhatsApp migrada."
            )

        if not empresa.whatsapp_access_token:
            raise ValueError(
                "La empresa no tiene un access token de WhatsApp configurado."
            )

        if not empresa.whatsapp_phone_number_id:
            raise ValueError(
                "La empresa no tiene Phone Number ID configurado."
            )

        config = ConfiguracionWhatsApp(
            empresa_id=empresa.id,
            activo=bool(empresa.whatsapp_conectado),
            whatsapp_business_account_id=empresa.whatsapp_waba_id,
            phone_number_id=empresa.whatsapp_phone_number_id,
            # El sistema legado no conserva el número visible por separado.
            numero_whatsapp=None,
            access_token_cifrado=SecretosService.cifrar(
                empresa.whatsapp_access_token
            ),
        )

        db.add(config)
        db.commit()
        db.refresh(config)

        return config
