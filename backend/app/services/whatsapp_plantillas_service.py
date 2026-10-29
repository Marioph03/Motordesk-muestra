"""Catálogo por empresa de las plantillas de WhatsApp que usa MotorDesk."""

import requests
from sqlalchemy.orm import Session

from app.models.whatsapp_plantilla import WhatsAppPlantilla
from app.services.whatsapp_config_service import WhatsAppConfigService
from app.services.whatsapp_service import WhatsAppService


class WhatsAppPlantillasService:
    """Mantiene referencias locales; no crea ni modifica plantillas en Meta."""

    # Catalogo funcional completo. Define que plantillas gestiona MotorDesk
    # y permite sincronizarlas con nombres historicos ya existentes en Meta.
    # No describe como se crean: esa responsabilidad pertenece al catalogo
    # PLANTILLAS_CREACION_META situado justo debajo.
    PLANTILLAS_MOTORDESK = {
        "FACTURA": {
            "nombre_meta": "motordesk_factura",
            "idioma": "es",
            "aliases_meta": ("factura",),
        },
        "PRESUPUESTO": {
            "nombre_meta": "motordesk_presupuesto",
            "idioma": "es",
            "aliases_meta": ("presupuesto",),
        },
        "GARANTIA": {
            "nombre_meta": "motordesk_garantia",
            "idioma": "es",
            "aliases_meta": ("garantia",),
        },
        "ORDEN_REPARACION": {
            "nombre_meta": "motordesk_orden_reparacion",
            "idioma": "es",
            "aliases_meta": ("orden_reparacion",),
        },
        "CONFIRMACION_CITA": {
            "nombre_meta": "motordesk_confirmacion_cita",
            "idioma": "es",
            "aliases_meta": ("confirmacion_cita",),
        },
        "RECORDATORIO_CITA": {
            "nombre_meta": "motordesk_recordatorio_cita",
            "idioma": "es",
            "aliases_meta": ("recordatorio_cita_taller",),
        },
        "REPROGRAMACION_CITA": {
            "nombre_meta": "motordesk_fecha_reprogramacion",
            "idioma": "es",
            "aliases_meta": ("fecha_reprogramacion",),
        },
    }

    PLANTILLAS_CREACION_META = {

    "FACTURA": {
        "categoria": "UTILITY",
        "header": {
            "format": "DOCUMENT",
        },
        "body": (
            "Hola\n\n"
            "{{1}},\n\n"
            "Te enviamos la factura {{2}} correspondiente al "
            "vehículo {{3}} con matrícula {{4}}.\n\n"
            "Importe total: {{5}} €\n\n"
            "Puedes consultar la factura en el documento adjunto.\n\n"
            "{{6}}\n\n"
            "Gracias por confiar en nosotros."
        ),
        "ejemplos": [
            "Nombre del cliente",
            "F-2026-000001",
            "Volkswagen Golf",
            "1234ABC",
            "484,00",
            "Taller MotorDesk",
        ],
    },

    "PRESUPUESTO": {
        "categoria": "UTILITY",
        "header": {
            "format": "DOCUMENT",
        },
        "body": (
            "Hola {{1}},\n\n"
            "Te enviamos el presupuesto {{2}} correspondiente al "
            "vehículo {{3}} con matrícula {{4}}.\n\n"
            "Importe total: {{5}} €\n\n"
            "Puedes consultar el detalle completo en el "
            "documento adjunto.\n\n"
            "{{6}}\n\n"
            "Gracias por confiar en nosotros."
        ),
        "ejemplos": [
            "Nombre del cliente",
            "PR-2026-000001",
            "Volkswagen Golf",
            "1234ABC",
            "484,00",
            "Taller MotorDesk",
        ],
    },

    "GARANTIA": {
        "categoria": "UTILITY",
        "header": {
            "format": "DOCUMENT",
        },
        "body": (
            "Hola\n\n"
            "{{1}},\n\n"
            "Te enviamos el documento de garantía {{2}} "
            "correspondiente al vehículo {{3}} con matrícula "
            "{{4}}.\n\n"
            "Puedes consultar el detalle completo de la garantía "
            "en el documento adjunto.\n\n"
            "{{5}}\n\n"
            "Gracias por confiar en nosotros."
        ),
        "ejemplos": [
            "Nombre del cliente",
            "G-2026-000001",
            "Volkswagen Golf",
            "1234ABC",
            "Taller MotorDesk",
        ],
    },

    "ORDEN_REPARACION": {
        "categoria": "UTILITY",
        "header": {
            "format": "DOCUMENT",
        },
        "body": (
            "Hola,\n\n"
            "{{1}}.\n\n"
            "Te enviamos la orden de reparación {{2}} "
            "correspondiente a tu vehículo.\n\n"
            "Vehículo: {{3}}\n"
            "Matrícula: {{4}}\n\n"
            "{{5}}\n\n"
            "Si tienes cualquier duda sobre esta reparación, "
            "puedes responder a este mensaje o contactar con nosotros."
        ),
        "ejemplos": [
            "Nombre del cliente",
            "OR-2026-000001",
            "Toyota Corolla",
            "4321XYZ",
            "Taller MotorDesk",
        ],
    },
    }

    @classmethod
    def inicializar_catalogo(
        cls,
        db: Session,
        empresa_id: int,
    ) -> list[WhatsAppPlantilla]:
        """Crea las referencias locales que falten para una empresa.

        La operación es idempotente: ejecutarla más de una vez no duplica
        registros. Las plantillas reales de Meta se crearán en un paso aparte.
        """
        config = WhatsAppConfigService.obtener(db, empresa_id)

        if config is None:
            raise ValueError("WhatsApp no está configurado para esta empresa.")

        resultado: list[WhatsAppPlantilla] = []

        for tipo, datos in cls.PLANTILLAS_MOTORDESK.items():
            existente = (
                db.query(WhatsAppPlantilla)
                .filter(
                    WhatsAppPlantilla.configuracion_id == config.id,
                    WhatsAppPlantilla.tipo == tipo,
                )
                .first()
            )

            if existente is not None:
                resultado.append(existente)
                continue

            plantilla = WhatsAppPlantilla(
                configuracion_id=config.id,
                tipo=tipo,
                nombre_meta=datos["nombre_meta"],
                idioma=datos["idioma"],
                estado="NO_CREADA",
            )
            db.add(plantilla)
            resultado.append(plantilla)

        db.commit()

        for plantilla in resultado:
            db.refresh(plantilla)

        return resultado

    @classmethod
    def listar(
        cls,
        db: Session,
        empresa_id: int,
    ) -> list[WhatsAppPlantilla]:
        """Lista las referencias de plantilla de la empresa autenticada."""
        config = WhatsAppConfigService.obtener(db, empresa_id)

        if config is None:
            return []

        return (
            db.query(WhatsAppPlantilla)
            .filter(WhatsAppPlantilla.configuracion_id == config.id)
            .order_by(WhatsAppPlantilla.tipo)
            .all()
        )

    @classmethod
    def obtener_pendientes_creacion(
        cls,
        db: Session,
        empresa_id: int,
    ) -> list[WhatsAppPlantilla]:
        """Devuelve las plantillas del catalogo que aun no existen en Meta.

        Este metodo consulta exclusivamente el ultimo estado guardado en
        MotorDesk. Para refrescarlo contra Meta se debe usar explicitamente
        ``sincronizar_con_meta``.
        """
        plantillas = cls.listar(db, empresa_id)

        return [
            plantilla
            for plantilla in plantillas
            if plantilla.estado == "NO_CREADA"
        ]

    @classmethod
    def resumen(
        cls,
        db: Session,
        empresa_id: int,
    ) -> dict[str, int]:
        """Resume el estado local de las plantillas de una empresa.

        No inicializa catalogos ni realiza llamadas de red, por lo que sirve
        para mostrar el grado de preparacion de WhatsApp sin efectos laterales.
        """
        plantillas = cls.listar(db, empresa_id)

        return {
            "total": len(plantillas),
            "aprobadas": sum(
                1
                for plantilla in plantillas
                if plantilla.estado == "APPROVED"
            ),
            "pendientes": sum(
                1
                for plantilla in plantillas
                if plantilla.estado == "PENDING"
            ),
            "rechazadas": sum(
                1
                for plantilla in plantillas
                if plantilla.estado == "REJECTED"
            ),
            "no_creadas": sum(
                1
                for plantilla in plantillas
                if plantilla.estado == "NO_CREADA"
            ),
        }

    @classmethod
    def obtener_plantillas_meta(
        cls,
        db: Session,
        empresa_id: int,
    ) -> list[dict]:
        """Lee plantillas de la WABA sin crear, modificar ni borrar en Meta."""
        config = WhatsAppConfigService.obtener(db, empresa_id)

        if config is None:
            raise ValueError("WhatsApp no está configurado para esta empresa.")

        if not config.activo:
            raise ValueError("La integración de WhatsApp está desactivada.")

        if not config.whatsapp_business_account_id:
            raise ValueError("La configuración no tiene WABA ID.")

        # El token se descifra solo en memoria y nunca se registra ni retorna.
        token = WhatsAppConfigService.obtener_token(db, empresa_id)
        url = (
            f"https://graph.facebook.com/{WhatsAppService.API_VERSION}/"
            f"{config.whatsapp_business_account_id}/message_templates"
        )

        try:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "fields": "id,name,status,language,category,components",
                    "limit": 100,
                },
                timeout=15,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                "No se pudo conectar con Meta para consultar las plantillas."
            ) from exc

        if not response.ok:
            raise RuntimeError(
                "Meta no ha permitido consultar las plantillas de WhatsApp Business."
            )

        return response.json().get("data", [])

    @classmethod
    def sincronizar_con_meta(
        cls,
        db: Session,
        empresa_id: int,
    ) -> list[WhatsAppPlantilla]:
        """Actualiza exclusivamente el estado local según la respuesta de Meta."""
        locales = cls.inicializar_catalogo(db, empresa_id)
        plantillas_meta = cls.obtener_plantillas_meta(db, empresa_id)

        indice_meta = {
            (plantilla.get("name"), plantilla.get("language")): plantilla
            for plantilla in plantillas_meta
        }

        for local in locales:
            datos_catalogo = cls.PLANTILLAS_MOTORDESK.get(local.tipo, {})
            nombres_candidatos = (
                local.nombre_meta,
                datos_catalogo.get("nombre_meta"),
                *datos_catalogo.get("aliases_meta", ()),
            )
            meta = next(
                (
                    indice_meta.get((nombre, local.idioma))
                    for nombre in nombres_candidatos
                    if nombre
                    and indice_meta.get((nombre, local.idioma)) is not None
                ),
                None,
            )

            if meta is None:
                local.estado = "NO_CREADA"
                continue

            # Cada empresa conserva el identificador realmente aprobado en
            # su propia WABA, aunque provenga de un catálogo legado.
            local.nombre_meta = meta["name"]
            local.idioma = meta.get("language") or local.idioma
            local.estado = (meta.get("status") or "DESCONOCIDO").upper()

        db.commit()

        for plantilla in locales:
            db.refresh(plantilla)

        return locales
    
    @classmethod
    def puede_crearse_automaticamente(
        cls,
        tipo: str,
    ) -> bool:
        return tipo in cls.PLANTILLAS_CREACION_META

    @classmethod
    def obtener_pendientes_creacion_automatica(
        cls,
        db: Session,
        empresa_id: int,
    ) -> list[WhatsAppPlantilla]:

        return [
            plantilla
            for plantilla in cls.obtener_pendientes_creacion(
                db,
                empresa_id,
            )
            if cls.puede_crearse_automaticamente(
                plantilla.tipo
            )
        ]
        
    @classmethod
    def subir_documento_ejemplo_meta(
        cls,
        db: Session,
        empresa_id: int,
        contenido_pdf: bytes,
        nombre_archivo: str = "motordesk_ejemplo.pdf",
    ) -> str:
        """
        Sube un PDF de ejemplo a Meta mediante Resumable Upload
        y devuelve el handle necesario para una plantilla DOCUMENT.

        Este método NO crea ninguna plantilla.
        """

        if not contenido_pdf:
            raise ValueError("El PDF de ejemplo está vacío.")

        config = WhatsAppConfigService.obtener(
            db,
            empresa_id,
        )

        if config is None:
            raise ValueError(
                "WhatsApp no está configurado para esta empresa."
            )

        if not config.activo:
            raise ValueError(
                "La integración de WhatsApp está desactivada."
            )

        token = WhatsAppConfigService.obtener_token(
            db,
            empresa_id,
        )

        # ---------------------------------------------------------
        # 1. Crear sesión de subida
        # ---------------------------------------------------------

        url_sesion = (
            f"https://graph.facebook.com/"
            f"{WhatsAppService.API_VERSION}/app/uploads"
        )

        try:
            response_sesion = requests.post(
                url_sesion,
                headers={
                    "Authorization": f"Bearer {token}",
                },
                params={
                    "file_length": len(contenido_pdf),
                    "file_type": "application/pdf",
                    "file_name": nombre_archivo,
                },
                timeout=15,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                "No se pudo conectar con Meta para iniciar "
                "la subida del PDF de ejemplo."
            ) from exc

        if not response_sesion.ok:
            raise RuntimeError(
                "Meta no ha permitido iniciar la subida "
                "del PDF de ejemplo."
            )

        upload_id = response_sesion.json().get("id")

        if not upload_id:
            raise RuntimeError(
                "Meta no ha devuelto un identificador "
                "para la sesión de subida."
            )

        # ---------------------------------------------------------
        # 2. Subir los bytes del PDF
        # ---------------------------------------------------------

        url_upload = (
            f"https://graph.facebook.com/"
            f"{WhatsAppService.API_VERSION}/{upload_id}"
        )

        try:
            response_upload = requests.post(
                url_upload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "file_offset": "0",
                    "Content-Type": "application/pdf",
                },
                data=contenido_pdf,
                timeout=30,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                "No se pudo conectar con Meta durante "
                "la subida del PDF de ejemplo."
            ) from exc

        if not response_upload.ok:
            raise RuntimeError(
                "Meta no ha permitido subir "
                "el PDF de ejemplo."
            )

        resultado = response_upload.json()

        handle = resultado.get("h")

        if not handle:
            raise RuntimeError(
                "Meta ha aceptado la subida, pero no ha "
                "devuelto el handle del documento."
            )

        return handle    
    
    @classmethod
    def crear_plantilla_meta_con_documento(
        cls,
        db: Session,
        empresa_id: int,
        tipo: str,
        contenido_pdf: bytes,
        nombre_archivo: str = "motordesk_ejemplo.pdf",
    ) -> dict:
        """
        Flujo completo para plantillas con HEADER DOCUMENT:

        1. Sube un PDF de ejemplo a Meta.
        2. Obtiene el header_handle.
        3. Crea la plantilla en Meta usando ese handle.

        No se debe ejecutar automáticamente al abrir la configuración.
        """

        if not contenido_pdf:
            raise ValueError(
                "El PDF de ejemplo está vacío."
            )

        header_handle = cls.subir_documento_ejemplo_meta(
            db=db,
            empresa_id=empresa_id,
            contenido_pdf=contenido_pdf,
            nombre_archivo=nombre_archivo,
        )

        return cls.crear_plantilla_meta(
            db=db,
            empresa_id=empresa_id,
            tipo=tipo,
            header_handle=header_handle,
        )
    
    @classmethod
    def crear_plantilla_meta(
        cls,
        db: Session,
        empresa_id: int,
        tipo: str,
        header_handle: str,
    ) -> dict:

        tipo = tipo.upper().strip()
        
        if not header_handle:
            raise ValueError(
                "Es obligatorio indicar el header_handle "
                "del PDF de ejemplo."
            )

        if not cls.puede_crearse_automaticamente(tipo):
            raise ValueError(
                f"La plantilla {tipo} no está habilitada "
                "para creación automática."
            )

        config = WhatsAppConfigService.obtener(
            db,
            empresa_id,
        )

        if config is None:
            raise ValueError(
                "WhatsApp no está configurado para esta empresa."
            )

        if not config.activo:
            raise ValueError(
                "La integración de WhatsApp está desactivada."
            )

        if not config.whatsapp_business_account_id:
            raise ValueError(
                "La configuración de WhatsApp no tiene WABA ID."
            )

        plantilla_local = (
            db.query(WhatsAppPlantilla)
            .filter(
                WhatsAppPlantilla.configuracion_id == config.id,
                WhatsAppPlantilla.tipo == tipo,
            )
            .first()
        )

        if plantilla_local is None:
            raise ValueError(
                f"No existe la plantilla local {tipo}."
            )

        if plantilla_local.estado != "NO_CREADA":
            raise ValueError(
                f"La plantilla {tipo} tiene estado "
                f"{plantilla_local.estado} y no se puede crear de nuevo."
            )

        definicion = cls.PLANTILLAS_CREACION_META[tipo]

        token = WhatsAppConfigService.obtener_token(
            db,
            empresa_id,
        )

        url = (
            f"https://graph.facebook.com/"
            f"{WhatsAppService.API_VERSION}/"
            f"{config.whatsapp_business_account_id}/message_templates"
        )

        payload = {
            "name": plantilla_local.nombre_meta,
            "language": plantilla_local.idioma,
            "category": definicion["categoria"],
            "components": [
                {
                    "type": "HEADER",
                    "format": definicion["header"]["format"],
                    "example": {
                        "header_handle": [
                        header_handle
                    ]
                    },
                },
                {
                    "type": "BODY",
                    "text": definicion["body"],
                    "example": {
                        "body_text": [
                            definicion["ejemplos"]
                        ]
                    },
                },
            ],
        }

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )

        if not response.ok:
            raise RuntimeError(
             "Meta no ha permitido crear la plantilla "
                f"{tipo}."
            )

        resultado = response.json()

    # Normalmente una plantilla recién enviada queda pendiente
    # de revisión, pero guardamos el estado que devuelva Meta.
        plantilla_local.estado = (
            resultado.get("status") or "PENDING"
        ).upper()

        db.commit()
        db.refresh(plantilla_local)

        return {
            "plantilla": plantilla_local,
            "meta_id": resultado.get("id"),
            "estado": plantilla_local.estado,
        }
