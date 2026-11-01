from collections.abc import Iterator

from sqlalchemy import URL, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

if settings.database_url is not None:
    database_url = make_url(settings.database_url.get_secret_value())

    if database_url.drivername not in {
        "postgres",
        "postgresql",
        "postgresql+psycopg",
    }:
        raise ValueError("DATABASE_URL must use PostgreSQL with psycopg")

    database_url = database_url.set(drivername="postgresql+psycopg")
else:
    if settings.postgres_password is None:
        raise ValueError("POSTGRES_PASSWORD is required")

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.postgres_user,
        password=settings.postgres_password.get_secret_value(),
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
    )

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 5},
)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
