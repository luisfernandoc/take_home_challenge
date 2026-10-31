from dataclasses import dataclass

from app.users.domain.entities import User


@dataclass(frozen=True)
class UserResult:
    user: User
    pokemon_names: list[str]
