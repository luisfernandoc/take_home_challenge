from typing import Protocol
from uuid import UUID
from app.users.domain.entities import User

class UserRepository(Protocol):
    def save(self, user: User) -> None:
        """Saves a new user."""
        ...

    def get_by_id(self, user_id: UUID) -> User | None:
        """Gets a User by ID,"""
        ...

    def get_by_email(self, user_email: str) -> User | None:
        """Gets a User by email."""
        ...

    def list_all(self) -> list[User]:
        """Returns all users."""
        ...

    def update(self) -> None:
        """Updates the data of an existing User."""
        ...

    def delete(self) -> None:
        """Deletes a User by ID."""
        ...
