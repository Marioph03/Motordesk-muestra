from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class SecretosService:
    @staticmethod
    def _obtener_fernet() -> Fernet:
        clave = settings.encryption_key

        if not clave:
            raise RuntimeError(
                "ENCRYPTION_KEY no está configurada en esta instalación."
            )

        try:
            return Fernet(clave.encode())
        except (ValueError, TypeError) as exc:
            raise RuntimeError(
                "ENCRYPTION_KEY no es una clave Fernet válida."
            ) from exc

    @classmethod
    def cifrar(cls, valor: str) -> str:
        if not valor:
            raise ValueError("No se puede cifrar un valor vacío.")

        return cls._obtener_fernet().encrypt(
            valor.encode("utf-8")
        ).decode("utf-8")

    @classmethod
    def descifrar(cls, valor_cifrado: str) -> str:
        if not valor_cifrado:
            raise ValueError("No existe ningún valor cifrado.")

        try:
            return cls._obtener_fernet().decrypt(
                valor_cifrado.encode("utf-8")
            ).decode("utf-8")
        except InvalidToken as exc:
            raise RuntimeError(
                "No se ha podido descifrar el secreto."
            ) from exc