from uuid import UUID

from app.users.domain.entities import User
from app.users.domain.exceptions import UserNotFoundError


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._users: dict[UUID, User] = {}

    def save(self, user: User) -> None:
        self._users[user.id] = user

    def get_by_id(self, user_id: UUID) -> User | None:
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    def list_all(self) -> list[User]:
        return list(self._users.values())

    def update(self, user: User) -> None:
        if user.id not in self._users:
            raise UserNotFoundError("User not found.")

        self._users[user.id] = user

    def delete(self, user_id: UUID) -> None:
        if user_id not in self._users:
            raise UserNotFoundError("User not found.")

        del self._users[user_id]
