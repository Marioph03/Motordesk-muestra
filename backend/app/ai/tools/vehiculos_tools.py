from sqlalchemy.orm import Session

from app.models.vehiculo import Vehiculo


VEHICULOS_TOOLS = [

    {
        "type": "function",

        "function": {

            "name": "buscar_vehiculo",

            "description": (
                "Busca vehículos registrados en MotorDesk "
                "por matrícula, bastidor, marca o modelo."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "texto": {
                        "type": "string",
                        "description": (
                            "Matrícula, bastidor, marca, "
                            "modelo o texto de búsqueda."
                        )
                    }

                },

                "required": [
                    "texto"
                ],

                "additionalProperties": False
            }
        }
    },


    {
        "type": "function",

        "function": {

            "name":
                "obtener_vehiculos_cliente",

            "description": (
                "Obtiene todos los vehículos asociados "
                "a un cliente concreto. Utilízala cuando "
                "el cliente ya ha sido identificado y "
                "se necesite consultar sus vehículos."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "cliente_id": {
                        "type": "integer",
                        "description": (
                            "ID interno del cliente "
                            "en MotorDesk."
                        )
                    }

                },

                "required": [
                    "cliente_id"
                ],

                "additionalProperties": False
            }
        }
    }

]


def buscar_vehiculo(
    db: Session,
    texto: str
) -> list[dict]:

    texto = texto.strip()

    if not texto:
        return []


    patron = f"%{texto}%"


    vehiculos = (

        db.query(Vehiculo)

        .filter(

            Vehiculo.matricula.ilike(
                patron
            )

            |

            Vehiculo.bastidor.ilike(
                patron
            )

            |

            Vehiculo.marca.ilike(
                patron
            )

            |

            Vehiculo.modelo.ilike(
                patron
            )

        )

        .limit(10)

        .all()

    )


    resultado = []


    for vehiculo in vehiculos:

        propietario = None


        if getattr(
            vehiculo,
            "cliente",
            None
        ):

            propietario = {

                "id":
                    vehiculo.cliente.id,

                "nombre":
                    vehiculo.cliente.nombre,

                "apellidos":
                    getattr(
                        vehiculo.cliente,
                        "apellidos",
                        None
                    )
            }


        resultado.append({

            "id":
                vehiculo.id,

            "matricula":
                vehiculo.matricula,

            "marca":
                vehiculo.marca,

            "modelo":
                vehiculo.modelo,

            "bastidor":
                getattr(
                    vehiculo,
                    "bastidor",
                    None
                ),

            "propietario":
                propietario

        })


    return resultado


def obtener_vehiculos_cliente(
    db: Session,
    cliente_id: int
) -> list[dict]:

    if not cliente_id:
        return []


    vehiculos = (

        db.query(Vehiculo)

        .filter(
            Vehiculo.cliente_id
            == cliente_id
        )

        .order_by(
            Vehiculo.id.desc()
        )

        .all()

    )


    return [

        {
            "id":
                vehiculo.id,

            "matricula":
                vehiculo.matricula,

            "marca":
                vehiculo.marca,

            "modelo":
                vehiculo.modelo,

            "bastidor":
                getattr(
                    vehiculo,
                    "bastidor",
                    None
                )

        }

        for vehiculo
        in vehiculos

    ]
"""Herramientas IA de búsqueda de vehículos y relación con su propietario."""
