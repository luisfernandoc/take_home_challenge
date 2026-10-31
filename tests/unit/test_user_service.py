from unittest.mock import Mock

import pytest

from app.users.application.exceptions import (
    PokemonNotFoundError,
    PokemonProviderUnavailableError,
)
from app.users.application.service import UserService
from app.users.domain.exceptions import EmailAlreadyRegisteredError
from app.users.infrastructure.repositories import InMemoryUserRepository


def test_create_user_stores_hash_and_pokemon_ids(
    service: UserService,
    repository: InMemoryUserRepository,
    password_hasher: Mock,
) -> None:
    result = service.create_user(
        name="Ana",
        email="ana@example.com",
        password="password-ficticia-de-prueba",
        pokemon_ids=[1, 25],
    )

    stored_user = repository.get_by_id(result.user.id)

    assert stored_user is not None
    assert stored_user.name == "Ana"
    assert stored_user.email == "ana@example.com"
    assert stored_user.password_hash == "hash-de-prueba"
    assert stored_user.pokemon_ids == [1, 25]
    assert result.pokemon_names == ["bulbasaur", "pikachu"]

    password_hasher.hash.assert_called_once_with("password-ficticia-de-prueba")


def test_create_user_rejects_duplicate_email(
    service: UserService,
    repository: InMemoryUserRepository,
    password_hasher: Mock,
) -> None:
    original = service.create_user(
        name="Ana",
        email="ana@example.com",
        password="password-ficticia-de-prueba",
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        service.create_user(
            name="Otra persona",
            email="ana@example.com",
            password="otra-password-ficticia",
        )

    assert repository.list_all() == [original.user]
    assert password_hasher.hash.call_count == 1


def test_update_name_preserves_password_and_pokemons(
    service: UserService,
    repository: InMemoryUserRepository,
) -> None:
    original = service.create_user(
        name="Ana",
        email="ana@example.com",
        password="password-ficticia-de-prueba",
        pokemon_ids=[25],
    )

    updated = service.update_user(
        original.user.id,
        name="Ana María",
    )

    stored_user = repository.get_by_id(original.user.id)

    assert stored_user is not None
    assert stored_user.name == "Ana María"
    assert stored_user.email == original.user.email
    assert stored_user.password_hash == original.user.password_hash
    assert stored_user.pokemon_ids == [25]
    assert updated.pokemon_names == ["pikachu"]


@pytest.mark.parametrize(
    ("new_ids", "expected_names"),
    [
        ([150], ["mewtwo"]),
        ([], []),
    ],
)
def test_update_replaces_pokemon_assignments(
    service: UserService,
    repository: InMemoryUserRepository,
    new_ids: list[int],
    expected_names: list[str],
) -> None:
    original = service.create_user(
        name="Ana",
        email="ana@example.com",
        password="password-ficticia-de-prueba",
        pokemon_ids=[1, 25],
    )

    updated = service.update_user(
        original.user.id,
        pokemon_ids=new_ids,
    )

    stored_user = repository.get_by_id(original.user.id)

    assert stored_user is not None
    assert stored_user.pokemon_ids == new_ids
    assert stored_user.password_hash == original.user.password_hash
    assert updated.pokemon_names == expected_names


@pytest.mark.parametrize(
    "error_type",
    [
        PokemonNotFoundError,
        PokemonProviderUnavailableError,
    ],
)
def test_create_user_does_not_save_when_pokemon_lookup_fails(
    service: UserService,
    repository: InMemoryUserRepository,
    pokemon_client: Mock,
    password_hasher: Mock,
    error_type: type[Exception],
) -> None:
    pokemon_client.get_name_by_id.side_effect = error_type("Error simulado de PokéAPI")

    with pytest.raises(error_type):
        service.create_user(
            name="Ana",
            email="ana@example.com",
            password="password-ficticia-de-prueba",
            pokemon_ids=[25],
        )

    assert repository.list_all() == []
    password_hasher.hash.assert_not_called()


@pytest.mark.parametrize(
    "error_type",
    [
        PokemonNotFoundError,
        PokemonProviderUnavailableError,
    ],
)
def test_update_user_preserves_data_when_pokemon_lookup_fails(
    service: UserService,
    repository: InMemoryUserRepository,
    pokemon_client: Mock,
    error_type: type[Exception],
) -> None:
    original = service.create_user(
        name="Ana",
        email="ana@example.com",
        password="password-ficticia-de-prueba",
        pokemon_ids=[25],
    )

    pokemon_client.get_name_by_id.side_effect = error_type("Error simulado de PokéAPI")

    with pytest.raises(error_type):
        service.update_user(
            original.user.id,
            name="Nombre que no debe guardarse",
            email="nuevo@example.com",
            pokemon_ids=[150],
        )

    stored_user = repository.get_by_id(original.user.id)

    assert stored_user == original.user
    assert stored_user is not None
    assert stored_user.name == "Ana"
    assert stored_user.email == "ana@example.com"
    assert stored_user.pokemon_ids == [25]
