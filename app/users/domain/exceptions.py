class EmailAlreadyRegisteredError(Exception):
    """El correo ya pertenece a un usuario."""


class UserNotFoundError(Exception):
    """No se encontró el usuario solicitado."""
