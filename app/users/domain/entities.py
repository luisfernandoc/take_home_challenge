from dataclasses import dataclass, field
from uuid import UUID

@dataclass()
class User:
    id: UUID
    name: str
    email: str
    password_hash: str | None = field(
        default=None,
        repr=False,
    )
