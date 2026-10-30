from dataclasses import replace
from uuid import UUID, uuid4

from app.users.application.password_hasher import PasswordHasher
from app.users.application.pokemon_client import PokemonClient
from app.users.domain.entities import User
from app.users.domain.exceptions import EmailAlreadyRegisteredError, UserNotFoundError
from app.users.domain.repositories import UserRepository

class UserService:
    def __init__(
        self,
        repository: UserRepository,
        password_hasher: PasswordHasher,
        pokemon_client: PokemonClient,
    ) -> None:
        self._repository = repository
        self._password_hasher = password_hasher
        self._pokemon_client = pokemon_client

    def create_user(self, name: str, email: str, password: str,) -> User:
        existing_user = self._repository.get_by_email(email)

        if existing_user is not None:
            raise EmailAlreadyRegisteredError(
                "Email already registered."
            )

        password_hash = self._password_hasher.hash(password)

        user = User(
            id=uuid4(),
            name=name,
            email=email,
            password_hash=password_hash,
        )

        self._repository.save(user)

        return user
    
    def list_users(self) -> list[User]:
        return self._repository.list_all()

    def get_user_by_id(self, user_id: UUID) -> User:
            user = self._repository.get_by_id(user_id)
    
            if user is None:
                raise UserNotFoundError("User not found.")
    
            return user
    
    def get_user_by_email(self, email: str) -> User:
        user = self._repository.get_by_email(email)

        if user is None:
            raise UserNotFoundError("User not found.")

        return user

    def update_user(
        self,
        user_id: UUID,
        *,
        name: str | None = None,
        email: str | None = None,
    ) -> User:
        user = self.get_user_by_id(user_id)

        if email is not None:
            existing_user = self._repository.get_by_email(email)

            if (
                existing_user is not None
                and existing_user.id != user.id
            ):
                raise EmailAlreadyRegisteredError(
                    "Email already registered"
                )

        updated_user = replace(
            user,
            name=name if name is not None else user.name,
            email=email if email is not None else user.email,
        )

        self._repository.update(updated_user)

        return updated_user

    def delete_user(self, user_id: UUID) -> None:
        self.get_user_by_id(user_id)

        self._repository.delete(user_id)

    def set_user_pokemons(
        self,
        user_id: UUID,
        pokemon_ids: list[int],
    ) -> list[str]:
        user = self.get_user_by_id(user_id)

        if any(
            type(pokemon_id) is not int or pokemon_id <= 0 for pokemon_id in pokemon_ids
        ):
            raise ValueError(
                "IDs of the Pokemon should be positive integers"
            )

        if len(pokemon_ids) != len(set(pokemon_ids)):
            raise ValueError(
                "The list of IDs can't contain repeated values"
            )

        names = [
            self._pokemon_client.get_name_by_id(pokemon_id) for pokemon_id in pokemon_ids
        ]

        updated_user = replace(
            user,
            pokemon_ids=list(pokemon_ids),  
        )

        self._repository.update(updated_user)

        return names

    def get_user_pokemon_names(self, user_id: UUID) -> list[str]:
        user = self.get_user_by_id(user_id)

        return [
            self._pokemon_client.get_name_by_id(pokemon_id) for pokemon_id in user.pokemon_ids
        ]
