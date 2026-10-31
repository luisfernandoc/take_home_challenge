from app.users.infrastructure.password_hasher import (
    Argon2PasswordHasher,
)


def test_hash_can_be_verified(
    real_password_hasher: Argon2PasswordHasher,
) -> None:
    password = "password-ficticia-de-prueba"

    hashed = real_password_hasher.hash(password)

    assert hashed != password
    assert real_password_hasher.verify(password, hashed)


def test_wrong_password_is_rejected(
    real_password_hasher: Argon2PasswordHasher,
) -> None:
    hashed = real_password_hasher.hash("password-ficticia-de-prueba")

    assert not real_password_hasher.verify(
        "otra-password",
        hashed,
    )


def test_same_password_produces_different_valid_hashes(
    real_password_hasher: Argon2PasswordHasher,
) -> None:
    password = "password-ficticia-de-prueba"

    first = real_password_hasher.hash(password)
    second = real_password_hasher.hash(password)

    assert first != second
    assert real_password_hasher.verify(password, first)
    assert real_password_hasher.verify(password, second)
