from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine

from tests.config import get_test_settings


def create_test_engine() -> Engine:
    settings = get_test_settings()

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.postgres_user,
        password=settings.postgres_password.get_secret_value(),
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )