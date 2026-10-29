import os


class VerifactuConfig:

    NOMBRE_SISTEMA = "MotorDesk"
    ID_SISTEMA = "MD"
    VERSION = "1.0.0"

    NUMERO_INSTALACION = "1"

    TIPO_USO_POSIBLE_SOLO_VERIFACTU = "S"
    TIPO_USO_POSIBLE_MULTI_OT = "N"
    INDICADOR_MULTIPLES_OT = "N"

    NOMBRE_PRODUCTOR = "MotorDesk"
    NIF_PRODUCTOR = os.getenv(
        "VERIFACTU_PRODUCTOR_NIF",
        ""
    )

    ENVIRONMENT = os.getenv(
        "VERIFACTU_ENV",
        "TEST"
    )

    CERT_PATH = os.getenv(
        "VERIFACTU_CERT_PATH",
        ""
    )

    CERT_PASSWORD = os.getenv(
        "VERIFACTU_CERT_PASSWORD",
        ""
    )

    TEST_ENDPOINT = (
        "https://prewww1.aeat.es/"
        "wlpl/TIKE-CONT/ws/"
        "SistemaFacturacion/"
        "VerifactuSOAP"
    )

    # Endpoint productivo publicado en el WSDL de la AEAT. Nunca se usa salvo
    # con VERIFACTU_ENV=PROD y la doble confirmación en configuración.
    PROD_ENDPOINT = os.getenv(
        "VERIFACTU_PROD_ENDPOINT",
        "https://www1.agenciatributaria.gob.es/"
        "wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP",
    )
"""Configuración específica de VERI*FACTU, separada del resto de la aplicación."""
