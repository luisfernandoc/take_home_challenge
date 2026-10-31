from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import EmailStr

from app.users.application.exceptions import PokemonNotFoundError
from app.users.application.results import UserResult
from app.users.application.service import UserService
from app.users.presentation.dependencies import get_user_service
from app.users.presentation.schemas import (
    UserCreate,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["Users"])

UserServiceDependency = Annotated[
    UserService,
    Depends(get_user_service),
]


def to_user_response(result: UserResult) -> UserResponse:
    return UserResponse(
        id=result.user.id,
        name=result.user.name,
        email=result.user.email,
        pokemons=result.pokemon_names,
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    data: UserCreate,
    service: UserServiceDependency,
) -> UserResponse:
    try:
        result = service.create_user(
            name=data.name,
            email=str(data.email),
            password=data.password.get_secret_value(),
            pokemon_ids=data.pokemon_ids,
        )
    except PokemonNotFoundError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return to_user_response(result)


@router.get("", response_model=list[UserResponse])
def list_users(
    service: UserServiceDependency,
) -> list[UserResponse]:
    results = service.list_user_results()

    return [to_user_response(result) for result in results]


@router.get("/by-email", response_model=UserResponse)
def get_user_by_email(
    email: EmailStr,
    service: UserServiceDependency,
) -> UserResponse:
    result = service.get_user_result_by_email(str(email))

    return to_user_response(result)


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: UUID,
    service: UserServiceDependency,
) -> UserResponse:
    result = service.get_user_result_by_id(user_id)

    return to_user_response(result)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    data: UserUpdate,
    service: UserServiceDependency,
) -> UserResponse:
    try:
        result = service.update_user(
            user_id,
            name=data.name,
            email=str(data.email) if data.email is not None else None,
            pokemon_ids=data.pokemon_ids,
        )
    except PokemonNotFoundError as error:
        status_code = 422 if data.pokemon_ids is not None else 502

        raise HTTPException(
            status_code=status_code,
            detail=str(error),
        ) from error

    return to_user_response(result)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_user(
    user_id: UUID,
    service: UserServiceDependency,
) -> Response:
    service.delete_user(user_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
