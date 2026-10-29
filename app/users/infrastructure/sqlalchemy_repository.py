from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.users.domain.entities import User
from app.users.domain.exceptions import (
    EmailAlreadyRegisteredError,
    UserNotFoundError,
)
from app.users.infrastructure.models import UserModel


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, user: User) -> None:
        model = UserModel(
            id=user.id,
            name=user.name,
            email=user.email,
            password_hash=user.password_hash,
        )

        self._session.add(model)
        self._commit()

    def get_by_id(self, user_id: UUID) -> User | None:
        model = self._session.get(UserModel, user_id)

        if model is None:
            return None

        return self._to_entity(model)

    def get_by_email(self, email: str) -> User | None:
        statement = select(UserModel).where(
            UserModel.email == email
        )

        model = self._session.scalar(statement)

        if model is None:
            return None

        return self._to_entity(model)

    def list_all(self) -> list[User]:
        statement = select(UserModel).order_by(UserModel.id)

        models = self._session.scalars(statement).all()

        return [self._to_entity(model) for model in models]

    def update(self, user: User) -> None:
        model = self._session.get(UserModel, user.id)

        if model is None:
            raise UserNotFoundError("No se encontró el usuario")

        model.name = user.name
        model.email = user.email

        self._commit()

    def delete(self, user_id: UUID) -> None:
        model = self._session.get(UserModel, user_id)

        if model is None:
            raise UserNotFoundError("No se encontró el usuario")

        self._session.delete(model)
        self._commit()

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            name=model.name,
            email=model.email,
            password_hash=model.password_hash,
        )

    def _commit(self) -> None:
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()

            diagnostic = getattr(error.orig, "diag", None)
            constraint_name = getattr(
                diagnostic,
                "constraint_name",
                None,
            )

            if constraint_name == "uq_users_email":
                raise EmailAlreadyRegisteredError(
                    "El correo ya está registrado"
                ) from error

            raise
