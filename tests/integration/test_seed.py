from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.users.infrastructure.models import UserModel
from scripts import seed


def test_seed_is_idempotent_and_preserves_existing_data(
    db_session: Session,
    password_hasher: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    email = f"{uuid4()}@example.com"

    monkeypatch.setattr(
        seed,
        "SEED_USERS",
        (
            (
                "Test Trainer",
                email,
                [1, 25],
            ),
        ),
    )

    assert seed.seed_users(db_session, password_hasher) == 1

    user = db_session.scalar(
        select(UserModel).where(UserModel.email == email)
    )

    assert user is not None
    assert user.pokemon_ids == [1, 25]
    assert user.password_hash == "hash-de-prueba"

    original_id = user.id
    original_hash = user.password_hash

    user.name = "Updated Trainer"
    db_session.flush()

    assert seed.seed_users(db_session, password_hasher) == 0

    db_session.refresh(user)

    assert user.id == original_id
    assert user.name == "Updated Trainer"
    assert user.password_hash == original_hash
