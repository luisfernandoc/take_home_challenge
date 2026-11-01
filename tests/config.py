from functools import lru_cache

from app.core.config import PROJECT_ROOT, Settings


@lru_cache
def get_test_settings() -> Settings:
    env_file = PROJECT_ROOT / ".env.test"

    if not env_file.is_file():
        raise RuntimeError("Falta .env.test en la raíz del proyecto")

    settings = Settings(_env_file=env_file)

    if settings.database_url is not None:
        raise ValueError("Tests must use explicit PostgreSQL test settings, not DATABASE_URL")

    if settings.postgres_db is None or not settings.postgres_db.endswith("_test"):
        raise ValueError("The test database name must end with '_test'")

    if not settings.postgres_db.endswith("_test"):
        raise ValueError("La base de pruebas debe terminar en '_test'")

    return settings
