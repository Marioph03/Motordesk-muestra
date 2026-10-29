from sqlalchemy.orm import Session

from app.models.cliente import Cliente


CLIENTES_TOOLS = [

    {
        "type": "function",

        "function": {

            "name": "buscar_cliente",

            "description": (
                "Busca clientes registrados en MotorDesk "
                "por nombre, apellidos, DNI/NIF, teléfono "
                "o email."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "texto": {
                        "type": "string",
                        "description": (
                            "Texto utilizado para localizar "
                            "al cliente."
                        )
                    }

                },

                "required": [
                    "texto"
                ],

                "additionalProperties": False
            }
        }
    }

]


def buscar_cliente(
    db: Session,
    texto: str
) -> list[dict]:

    texto = texto.strip()

    if not texto:
        return []


    patron = f"%{texto}%"


    clientes = (

        db.query(Cliente)

        .filter(

            Cliente.nombre.ilike(
                patron
            )

            |

            Cliente.apellidos.ilike(
                patron
            )

            |

            Cliente.dni.ilike(
                patron
            )

            |

            Cliente.telefono.ilike(
                patron
            )

            |

            Cliente.email.ilike(
                patron
            )

        )

        .limit(10)

        .all()

    )


    return [

        {
            "id":
                cliente.id,

            "nombre":
                cliente.nombre,

            "apellidos":
                cliente.apellidos,

            "dni":
                cliente.dni,

            "telefono":
                cliente.telefono,

            "email":
                cliente.email
        }

        for cliente in clientes

    ]
"""Herramientas IA de búsqueda de clientes, sujetas al control de permisos."""
