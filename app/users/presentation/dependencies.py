from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db_session
from app.users.application.service import UserService
from app.users.application.pokemon_client import PokemonClient
from app.users.application.password_hasher import PasswordHasher
from app.users.infrastructure.password_hasher import Argon2PasswordHasher
from app.users.domain.repositories import UserRepository
from app.users.infrastructure.sqlalchemy_repository import SqlAlchemyUserRepository

def get_user_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> UserRepository:
    return SqlAlchemyUserRepository(session=session)
def get_password_hasher() -> PasswordHasher:
    return Argon2PasswordHasher()

def get_pokemon_client(request: Request) -> PokemonClient:
    return request.app.state.pokemon_client

def get_user_service(
    repository: Annotated[
        UserRepository,
        Depends(get_user_repository),
    ],
    password_hasher: Annotated[
        PasswordHasher,
        Depends(get_password_hasher),
    ],
    pokemon_client: Annotated[
        PokemonClient,
        Depends(get_pokemon_client),
    ],
) -> UserService:
    return UserService(
        repository=repository,
        password_hasher=password_hasher,
        pokemon_client=pokemon_client,
    )
