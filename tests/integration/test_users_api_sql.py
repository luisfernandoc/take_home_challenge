from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy.orm import Session

from app.users.infrastructure.models import UserModel
from app.users.infrastructure.password_hasher import (
    Argon2PasswordHasher,
)

pytestmark = pytest.mark.anyio


async def test_user_crud_with_postgresql(
    sql_client: httpx.AsyncClient,
    db_session: Session,
    real_password_hasher: Argon2PasswordHasher,
    user_payload: dict,
) -> None:
    payload = {
        **user_payload,
        "email": f"{uuid4()}@example.com",
        "pokemon_ids": [1, 25],
    }

    # Crear mediante HTTP.
    created_response = await sql_client.post(
        "/users",
        json=payload,
    )
    assert created_response.status_code == 201

    created = created_response.json()
    user_id = UUID(created["id"])

    assert created["pokemons"] == ["bulbasaur", "pikachu"]
    assert set(created) == {
        "id",
        "name",
        "email",
        "pokemons",
    }

    # Verificar directamente lo almacenado.
    stored = db_session.get(UserModel, user_id)

    assert stored is not None
    assert stored.pokemon_ids == [1, 25]
    assert stored.password_hash is not None
    assert stored.password_hash != payload["password"]
    assert real_password_hasher.verify(
        payload["password"],
        stored.password_hash,
    )

    original_hash = stored.password_hash

    # Consultar mediante HTTP.
    retrieved = await sql_client.get(f"/users/{user_id}")

    assert retrieved.status_code == 200
    assert retrieved.json() == created

    # Actualizar mediante HTTP.
    updated = await sql_client.patch(
        f"/users/{user_id}",
        json={
            "name": "Ana María",
            "pokemon_ids": [150],
        },
    )

    assert updated.status_code == 200
    assert updated.json()["name"] == "Ana María"
    assert updated.json()["pokemons"] == ["mewtwo"]

    # Volver a leer los valores desde PostgreSQL.
    db_session.refresh(stored)

    assert stored.name == "Ana María"
    assert stored.pokemon_ids == [150]
    assert stored.password_hash == original_hash

    # Eliminar mediante HTTP.
    deleted = await sql_client.delete(f"/users/{user_id}")

    assert deleted.status_code == 204
    assert deleted.content == b""

    missing = await sql_client.get(f"/users/{user_id}")

    assert missing.status_code == 404

    db_session.expire_all()
    assert db_session.get(UserModel, user_id) is None
