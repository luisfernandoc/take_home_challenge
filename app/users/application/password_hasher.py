from typing import Protocol


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str:
        """Genera un hash para almacenar."""
        ...

    def verify(self, password: str, password_hash: str) -> bool:
        """Comprueba si una contraseña corresponde al hash."""
        ...
