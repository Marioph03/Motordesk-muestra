from app.database.database import SessionLocal
from app.seeds.permisos_seed import seed_permisos


def run():
    db = SessionLocal()

    try:
        seed_permisos(db)

        print(
            "Roles y permisos creados correctamente."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run()
"""Punto de ejecución manual para inicializar permisos en una instalación."""
