from collections.abc import AsyncGenerator, Callable, Iterator
from contextlib import ExitStack
from unittest.mock import Mock

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.infrastructure.clients.pokeapi_client import PokeApiClient
from app.infrastructure.database import get_db_session
from app.main import app
from app.users.application.password_hasher import PasswordHasher
from app.users.application.pokemon_client import PokemonClient
from app.users.application.service import UserService
from app.users.infrastructure.password_hasher import (
    Argon2PasswordHasher,
)
from app.users.infrastructure.repositories import InMemoryUserRepository
from app.users.infrastructure.sqlalchemy_repository import (
    SqlAlchemyUserRepository,
)
from app.users.presentation.dependencies import (
    get_password_hasher,
    get_pokemon_client,
    get_user_service,
)
from tests.config import get_test_settings
from tests.database import create_test_engine


@pytest.fixture
def repository() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def password_hasher() -> Mock:
    hasher = Mock(spec=PasswordHasher)
    hasher.hash.return_value = "hash-de-prueba"

    return hasher


@pytest.fixture
def pokemon_client() -> Mock:
    client = Mock(spec=PokemonClient)

    names = {
        1: "bulbasaur",
        25: "pikachu",
        150: "mewtwo",
    }

    client.get_name_by_id.side_effect = names.__getitem__

    return client


@pytest.fixture
def service(
    repository: InMemoryUserRepository,
    password_hasher: Mock,
    pokemon_client: Mock,
) -> UserService:
    return UserService(
        repository=repository,
        password_hasher=password_hasher,
        pokemon_client=pokemon_client,
    )


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client(
    service: UserService,
) -> AsyncGenerator[httpx.AsyncClient]:
    def override_user_service() -> UserService:
        return service

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_user_service] = override_user_service

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as http_client:
            yield http_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    settings = get_test_settings()
    engine = create_test_engine()

    try:
        with engine.begin() as connection:
            database = connection.scalar(text("SELECT current_database()"))

            if database != settings.postgres_db:
                raise RuntimeError("La conexión no corresponde a la base de pruebas")

            config = Config("alembic.ini")
            config.attributes["connection"] = connection

            command.upgrade(config, "head")

        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Iterator[Session]:
    with test_engine.connect() as connection:
        transaction = connection.begin()

        session = Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )

        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture
def sql_repository(
    db_session: Session,
) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session=db_session)


@pytest.fixture
def pokeapi_client_factory() -> Iterator[
    Callable[
        [Callable[[httpx.Request], httpx.Response]],
        PokeApiClient,
    ]
]:
    with ExitStack() as stack:

        def create_client(
            handler: Callable[[httpx.Request], httpx.Response],
        ) -> PokeApiClient:
            http_client = stack.enter_context(
                httpx.Client(
                    base_url="https://pokeapi.test/api/v2/",
                    timeout=5.0,
                    transport=httpx.MockTransport(handler),
                )
            )

            return PokeApiClient(http_client=http_client)

        yield create_client


@pytest.fixture
def real_password_hasher() -> Argon2PasswordHasher:
    return Argon2PasswordHasher()


@pytest.fixture
def user_payload() -> dict:
    return {
        "name": "Ana",
        "email": "ana@example.com",
        "password": "password-ficticia-de-prueba",
        "pokemon_ids": [25],
    }


@pytest.fixture
async def sql_client(
    db_session: Session,
    pokemon_client: Mock,
    real_password_hasher: Argon2PasswordHasher,
) -> AsyncGenerator[httpx.AsyncClient]:
    def override_session() -> Session:
        return db_session

    def override_pokemon_client():
        return pokemon_client

    def override_password_hasher():
        return real_password_hasher

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides.clear()

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_pokemon_client] = override_pokemon_client
    app.dependency_overrides[get_password_hasher] = override_password_hasher

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as http_client:
            yield http_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
