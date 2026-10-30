from alembic import command
from alembic.config import Config
from sqlalchemy import text

from tests.config import get_test_settings
from tests.database import create_test_engine


def main() -> None:
    settings = get_test_settings()
    engine = create_test_engine()

    try:
        with engine.begin() as connection:
            database = connection.scalar(
                text("SELECT current_database()")
            )

            if database != settings.postgres_db:
                raise RuntimeError(
                    "La conexión no corresponde a la base de pruebas"
                )

            config = Config("alembic.ini")
            config.attributes["connection"] = connection

            command.upgrade(config, "head")

        print(
            f"Migraciones aplicadas correctamente en "
            f"{settings.postgres_db}"
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
