class ExcelCamposService:

    CAMPOS = {

        "clientes": [

            {
                "campo": "nombre",
                "label": "Nombre",
                "obligatorio": True,
            },

            {
                "campo": "apellidos",
                "label": "Apellidos",
                "obligatorio": False,
            },

            {
                "campo": "dni_nif",
                "label": "DNI / NIF",
                "obligatorio": False,
            },

            {
                "campo": "telefono",
                "label": "Teléfono",
                "obligatorio": False,
            },

            {
                "campo": "email",
                "label": "Email",
                "obligatorio": False,
            },

            {
                "campo": "direccion",
                "label": "Dirección",
                "obligatorio": False,
            },

            {
                "campo": "codigo_postal",
                "label": "Código postal",
                "obligatorio": False,
            },

            {
                "campo": "localidad",
                "label": "Localidad",
                "obligatorio": False,
            },

            {
                "campo": "provincia",
                "label": "Provincia",
                "obligatorio": False,
            },

            {
                "campo": "observaciones",
                "label": "Observaciones",
                "obligatorio": False,
            },

        ],


        "vehiculos": [

            {
                "campo": "matricula",
                "label": "Matrícula",
                "obligatorio": True,
            },

            {
                "campo": "marca",
                "label": "Marca",
                "obligatorio": False,
            },

            {
                "campo": "modelo",
                "label": "Modelo",
                "obligatorio": False,
            },

            {
                "campo": "version",
                "label": "Versión",
                "obligatorio": False,
            },

            {
                "campo": "bastidor",
                "label": "Bastidor",
                "obligatorio": False,
            },

            {
                "campo": "kilometros",
                "label": "Kilómetros",
                "obligatorio": False,
            },

            {
                "campo": "combustible",
                "label": "Combustible",
                "obligatorio": False,
            },

            {
                "campo": "cliente_dni_nif",
                "label": "DNI / NIF propietario",
                "obligatorio": True,
            },

        ],


        "proveedores": [

            {
                "campo": "nombre",
                "label": "Nombre / Razón social",
                "obligatorio": True,
            },

            {
                "campo": "nif_cif",
                "label": "NIF / CIF",
                "obligatorio": True,
            },

            {
                "campo": "telefono",
                "label": "Teléfono",
                "obligatorio": False,
            },

            {
                "campo": "email",
                "label": "Email",
                "obligatorio": False,
            },

            {
                "campo": "direccion",
                "label": "Dirección",
                "obligatorio": False,
            },

            {
                "campo": "localidad",
                "label": "Localidad",
                "obligatorio": False,
            },

            {
                "campo": "provincia",
                "label": "Provincia",
                "obligatorio": False,
            },

        ],


        "articulos": [

            {
                "campo": "referencia",
                "label": "Referencia",
                "obligatorio": True,
            },

            {
                "campo": "nombre",
                "label": "Nombre",
                "obligatorio": True,
            },

            {
                "campo": "descripcion",
                "label": "Descripción",
                "obligatorio": False,
            },

            {
                "campo": "stock_actual",
                "label": "Stock actual",
                "obligatorio": False,
            },

            {
                "campo": "stock_minimo",
                "label": "Stock mínimo",
                "obligatorio": False,
            },

            {
                "campo": "coste_unitario",
                "label": "Coste unitario",
                "obligatorio": False,
            },

        ],

    }


    @staticmethod
    def obtener_campos(
        tipo: str
    ):

        tipo = tipo.lower().strip()

        if tipo not in ExcelCamposService.CAMPOS:

            raise ValueError(
                "Tipo de importación no válido"
            )

        return ExcelCamposService.CAMPOS[
            tipo
        ]
"""Catálogo de campos MotorDesk disponibles para mapear columnas de Excel."""
