"""Usuario autenticable, rol y relaciones de planificación del equipo."""

from datetime import datetime, time

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
)

from sqlalchemy.orm import relationship

from app.database.database import Base


class Usuario(Base):
    """Miembro del equipo con acceso a MotorDesk según su rol y estado."""


    __tablename__ = "usuarios"


    # =========================================================
    # IDENTIFICACIÓN
    # =========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    nombre = Column(
        String(100),
        nullable=False
    )

    apellidos = Column(
        String(150),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False
    )


    # =========================================================
    # AUTENTICACIÓN
    # =========================================================

    password_hash = Column(
        String(255),
        nullable=False
    )

    rol = Column(
        String(50),
        nullable=False
    )

    activo = Column(
        Boolean,
        default=True
    )

    ultimo_acceso = Column(
        DateTime
    )

    avatar_url = Column(
        String(500),
        nullable=True
    )

    hora_entrada_predeterminada = Column(Time, nullable=False, default=lambda: time(8, 0))
    hora_salida_predeterminada = Column(Time, nullable=False, default=lambda: time(16, 0))


    # =========================================================
    # EMPRESA
    # =========================================================

    empresa_id = Column(
        Integer,
        ForeignKey("empresa.id"),
        nullable=True,
        index=True
    )

    empresa = relationship(
        "Empresa",
        back_populates="usuarios"
    )


    # =========================================================
    # FECHAS
    # =========================================================

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    actividades = relationship(
        "Actividad",
        back_populates="usuario"
    )

    ausencias = relationship(
        "AusenciaPersonal",
        back_populates="usuario",
        cascade="all, delete-orphan",
        order_by="AusenciaPersonal.fecha_inicio.desc()",
    )

    citas_asignadas = relationship(
        "Cita",
        secondary="cita_usuarios",
        back_populates="usuarios_asignados",
    )

    ordenes_asignadas = relationship(
        "OrdenReparacion",
        secondary="orden_usuarios",
        back_populates="usuarios_asignados",
    )
