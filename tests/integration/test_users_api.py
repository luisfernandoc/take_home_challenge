from unittest.mock import Mock
from uuid import uuid4

import httpx
import pytest

from app.users.application.exceptions import (
    PokemonProviderUnavailableError,
)
from app.users.application.service import UserService

pytestmark = pytest.mark.anyio

async def test_create_and_get_user(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/users",
        json={
            "name": "Ana",
            "email": "ana@example.com",
            "password": "password-ficticia-de-prueba",
            "pokemon_ids": [1, 25],
        },
    )

    assert response.status_code == 201

    created = response.json()

    assert created["name"] == "Ana"
    assert created["pokemons"] == ["bulbasaur", "pikachu"]

    assert set(created) == {
        "id",
        "name",
        "email",
        "pokemons",
    }

    response = await client.get(
        f"/users/{created['id']}"
    )

    assert response.status_code == 200
    assert response.json() == created

async def test_create_user_rejects_duplicate_pokemon_ids(
    client: httpx.AsyncClient,
    service: UserService,
) -> None:
    response = await client.post(
        "/users",
        json={
            "name": "Ana",
            "email": "ana@example.com",
            "password": "password-ficticia-de-prueba",
            "pokemon_ids": [25, 25],
        },
    )

    assert response.status_code == 422
    assert service.list_user_results() == []

async def test_create_user_returns_502_when_provider_fails(
    client: httpx.AsyncClient,
    pokemon_client: Mock,
    service: UserService,
) -> None:
    pokemon_client.get_name_by_id.side_effect = (
        PokemonProviderUnavailableError(
            "Error simulado de PokéAPI"
        )
    )

    response = await client.post(
        "/users",
        json={
            "name": "Ana",
            "email": "ana@example.com",
            "password": "password-ficticia-de-prueba",
            "pokemon_ids": [25],
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "No fue posible consultar PokéAPI"
    }
    assert service.list_user_results() == []

async def test_patch_user_replaces_pokemons(
    client: httpx.AsyncClient,
) -> None:
    created_response = await client.post(
        "/users",
        json={
            "name": "Ana",
            "email": "ana@example.com",
            "password": "password-ficticia-de-prueba",
            "pokemon_ids": [1, 25],
        },
    )
    assert created_response.status_code == 201

    created = created_response.json()

    response = await client.patch(
        f"/users/{created['id']}",
        json={"pokemon_ids": [150]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": created["id"],
        "name": "Ana",
        "email": "ana@example.com",
        "pokemons": ["mewtwo"],
    }

    persisted = await client.get(
        f"/users/{created['id']}"
    )

    assert persisted.status_code == 200
    assert persisted.json() == response.json()

@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": None},
        {"email": None},
        {"pokemon_ids": None},
    ],
)
async def test_patch_user_rejects_invalid_body(
    client: httpx.AsyncClient,
    payload: dict,
) -> None:
    created_response = await client.post(
        "/users",
        json={
            "name": "Ana",
            "email": "ana@example.com",
            "password": "password-ficticia-de-prueba",
            "pokemon_ids": [25],
        },
    )
    assert created_response.status_code == 201

    created = created_response.json()

    response = await client.patch(
        f"/users/{created['id']}",
        json=payload,
    )

    assert response.status_code == 422

    unchanged = await client.get(
        f"/users/{created['id']}"
    )

    assert unchanged.status_code == 200
    assert unchanged.json() == created

async def test_get_user_by_email(
    client: httpx.AsyncClient,
) -> None:
    created_response = await client.post(
        "/users",
        json={
            "name": "Ana",
            "email": "ana@example.com",
            "password": "password-ficticia-de-prueba",
            "pokemon_ids": [25],
        },
    )
    assert created_response.status_code == 201

    response = await client.get(
        "/users/by-email",
        params={"email": "ana@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == created_response.json()

async def test_delete_user(
    client: httpx.AsyncClient,
) -> None:
    created_response = await client.post(
        "/users",
        json={
            "name": "Ana",
            "email": "ana@example.com",
            "password": "password-ficticia-de-prueba",
        },
    )
    assert created_response.status_code == 201

    user_id = created_response.json()["id"]

    response = await client.delete(
        f"/users/{user_id}"
    )

    assert response.status_code == 204
    assert response.content == b""

    missing = await client.get(
        f"/users/{user_id}"
    )

    assert missing.status_code == 404

@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
async def test_unknown_user_returns_404(
    client: httpx.AsyncClient,
    method: str,
) -> None:
    url = f"/users/{uuid4()}"

    if method == "PATCH":
        response = await client.patch(
            url,
            json={"name": "Nuevo nombre"},
        )
    else:
        response = await client.request(method, url)

    assert response.status_code == 404
    assert "detail" in response.json()


async def test_unknown_email_returns_404(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/users/by-email",
        params={"email": "no-existe@example.com"},
    )

    assert response.status_code == 404

async def test_create_duplicate_email_returns_409(
    client: httpx.AsyncClient,
    user_payload: dict,
) -> None:
    first = await client.post(
        "/users",
        json=user_payload,
    )
    assert first.status_code == 201

    duplicate = await client.post(
        "/users",
        json=user_payload,
    )

    assert duplicate.status_code == 409

    listed = await client.get("/users")

    assert listed.status_code == 200
    assert listed.json() == [first.json()]

async def test_patch_cannot_use_another_users_email(
    client: httpx.AsyncClient,
    user_payload: dict,
) -> None:
    first = await client.post(
        "/users",
        json=user_payload,
    )
    assert first.status_code == 201

    second = await client.post(
        "/users",
        json={
            **user_payload,
            "name": "Luis",
            "email": "luis@example.com",
        },
    )
    assert second.status_code == 201

    second_user = second.json()

    response = await client.patch(
        f"/users/{second_user['id']}",
        json={
            "name": "Nombre que no debe guardarse",
            "email": user_payload["email"],
        },
    )

    assert response.status_code == 409

    unchanged = await client.get(
        f"/users/{second_user['id']}"
    )

    assert unchanged.status_code == 200
    assert unchanged.json() == second_user

async def test_patch_allows_keeping_own_email(
    client: httpx.AsyncClient,
    user_payload: dict,
) -> None:
    created = await client.post(
        "/users",
        json=user_payload,
    )
    assert created.status_code == 201

    user = created.json()

    response = await client.patch(
        f"/users/{user['id']}",
        json={
            "name": "Ana María",
            "email": user_payload["email"],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        **user,
        "name": "Ana María",
    }
