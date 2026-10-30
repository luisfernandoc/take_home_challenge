from dataclasses import replace
from uuid import UUID, uuid4

from app.users.application.password_hasher import PasswordHasher
from app.users.application.pokemon_client import PokemonClient
from app.users.application.results import UserResult
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

    def create_user(
        self,
        name: str,
        email: str,
        password: str,
        pokemon_ids: list[int] | None = None,
    ) -> UserResult:
        existing_user = self._repository.get_by_email(email)

        if existing_user is not None:
            raise EmailAlreadyRegisteredError(
                "El correo ya está registrado"
            )

        ids = list(pokemon_ids) if pokemon_ids is not None else []
        names = self._resolve_pokemon_names(ids)

        user = User(
            id=uuid4(),
            name=name,
            email=email,
            password_hash=self._password_hasher.hash(password),
            pokemon_ids=ids,
        )

        self._repository.save(user)

        return UserResult(
            user=user,
            pokemon_names=names,
        )

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
        pokemon_ids: list[int] | None = None,
    ) -> UserResult:
        user = self.get_user_by_id(user_id)

        if email is not None:
            existing_user = self._repository.get_by_email(email)

            if existing_user is not None and existing_user.id != user.id:
                raise EmailAlreadyRegisteredError(
                    "El correo ya está registrado"
                )

        ids = (
            list(pokemon_ids)
            if pokemon_ids is not None
            else list(user.pokemon_ids)
        )

        names = self._resolve_pokemon_names(ids)

        updated_user = replace(
            user,
            name=name if name is not None else user.name,
            email=email if email is not None else user.email,
            pokemon_ids=ids,
        )

        self._repository.update(updated_user)

        return UserResult(
            user=updated_user,
            pokemon_names=names,
        )

    def delete_user(self, user_id: UUID) -> None:
        self.get_user_by_id(user_id)

        self._repository.delete(user_id)

    def get_user_result_by_id(self, user_id: UUID) -> UserResult:
        user = self.get_user_by_id(user_id)

        return self._build_user_result(user)

    def get_user_result_by_email(self, email: str) -> UserResult:
        user = self.get_user_by_email(email)

        return self._build_user_result(user)

    def list_user_results(self) -> list[UserResult]:
        users = self._repository.list_all()

        return [self._build_user_result(user) for user in users]

    def _build_user_result(self, user: User) -> UserResult:
        return UserResult(
            user=user,
            pokemon_names=self._resolve_pokemon_names(
                user.pokemon_ids
            ),
        )

    def _resolve_pokemon_names(
        self,
        pokemon_ids: list[int],
    ) -> list[str]:
        if len(pokemon_ids) > 100:
            raise ValueError("No puedes asignar más de 100 Pokémon")

        if any(
            type(pokemon_id) is not int or pokemon_id <= 0
            for pokemon_id in pokemon_ids
        ):
            raise ValueError(
                "Los IDs de Pokémon deben ser enteros positivos"
            )

        if len(pokemon_ids) != len(set(pokemon_ids)):
            raise ValueError(
                "La lista no puede contener IDs repetidos"
            )

        return [
            self._pokemon_client.get_name_by_id(pokemon_id)
            for pokemon_id in pokemon_ids
        ]
