"""Infraestructura compartida de SQLAlchemy.

Los modelos heredan de ``Base`` y cada petición obtiene una sesión independiente
mediante ``get_db``. Los servicios deciden cuándo confirmar o revertir una
transacción; esta dependencia se limita a cerrar la sesión al terminar.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

DATABASE_URL = settings.database_url

# El engine es compartido por toda la aplicación. No abrir engines por servicio:
# se perderían el pool de conexiones y la configuración centralizada.
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    """Proporciona una sesión por petición y garantiza su cierre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
