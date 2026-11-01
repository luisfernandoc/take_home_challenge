from secrets import token_urlsafe
from uuid import uuid4

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.infrastructure.database import SessionLocal, engine
from app.users.application.password_hasher import PasswordHasher
from app.users.infrastructure.models import UserModel
from app.users.infrastructure.password_hasher import Argon2PasswordHasher

SEED_USERS = (
    (
        "Demo Trainer One",
        "trainer.one@example.com",
        [1, 25],
    ),
    (
        "Demo Trainer Two",
        "trainer.two@example.com",
        [4, 7],
    ),
)


def seed_users(
    session: Session,
    password_hasher: PasswordHasher,
) -> int:
    created_count = 0

    for name, email, pokemon_ids in SEED_USERS:
        statement = (
            insert(UserModel)
            .values(
                id=uuid4(),
                name=name,
                email=email,
                password_hash=password_hasher.hash(token_urlsafe(32)),
                pokemon_ids=list(pokemon_ids),
            )
            .on_conflict_do_nothing(constraint="uq_users_email")
            .returning(UserModel.id)
        )

        created_id = session.scalar(statement)

        if created_id is not None:
            created_count += 1

    return created_count


def main() -> None:
    try:
        password_hasher = Argon2PasswordHasher()

        with SessionLocal.begin() as session:
            created_count = seed_users(
                session=session,
                password_hasher=password_hasher,
            )

        print(f"Seed completed. Created users: {created_count}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
