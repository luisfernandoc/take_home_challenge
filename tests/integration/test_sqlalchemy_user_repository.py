from dataclasses import replace
from uuid import uuid4

import pytest

from app.users.domain.entities import User
from app.users.domain.exceptions import (
    EmailAlreadyRegisteredError,
)
from app.users.infrastructure.sqlalchemy_repository import (
    SqlAlchemyUserRepository,
)


@pytest.fixture
def user() -> User:
    user_id = uuid4()

    return User(
        id=user_id,
        name="Ana",
        email=f"{user_id}@example.com",
        password_hash="hash-ficticio-solo-para-testing",
        pokemon_ids=[1, 25],
    )


def test_save_and_retrieve_user(
    sql_repository: SqlAlchemyUserRepository,
    user: User,
) -> None:
    sql_repository.save(user)

    stored = sql_repository.get_by_id(user.id)

    assert stored == user
    assert sql_repository.get_by_email(user.email) == user


def test_update_user_preserves_password_hash(
    sql_repository: SqlAlchemyUserRepository,
    user: User,
) -> None:
    sql_repository.save(user)

    updated = replace(
        user,
        name="Ana María",
        pokemon_ids=[150],
    )

    sql_repository.update(updated)

    stored = sql_repository.get_by_id(user.id)

    assert stored is not None
    assert stored.name == "Ana María"
    assert stored.pokemon_ids == [150]
    assert stored.password_hash == user.password_hash


def test_duplicate_email_is_rejected_and_session_remains_usable(
    sql_repository: SqlAlchemyUserRepository,
    user: User,
) -> None:
    sql_repository.save(user)

    duplicate = replace(
        user,
        id=uuid4(),
        name="Otro usuario",
    )
    print(f'user email: {user.email}')
    print(f'duplicated email: {duplicate.email}')

    with pytest.raises(EmailAlreadyRegisteredError):
        sql_repository.save(duplicate)

    assert sql_repository.get_by_id(user.id) == user
    assert sql_repository.get_by_id(duplicate.id) is None


def test_delete_user(
    sql_repository: SqlAlchemyUserRepository,
    user: User,
) -> None:
    sql_repository.save(user)

    sql_repository.delete(user.id)

    assert sql_repository.get_by_id(user.id) is None
    assert sql_repository.get_by_email(user.email) is None
