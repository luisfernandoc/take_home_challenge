from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import EmailStr

from app.users.application.service import UserService
from app.users.domain.exceptions import EmailAlreadyRegisteredError, UserNotFoundError
from app.users.presentation.dependencies import get_user_service
from app.users.presentation.schemas import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])

UserServiceDependency = Annotated[
    UserService,
    Depends(get_user_service),
]

@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    data: UserCreate,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    try:
        user = service.create_user(
            name=data.name,
            email=str(data.email),
            password=data.password.get_secret_value(),
        )
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return UserResponse.model_validate(user)

@router.get("", response_model=list[UserResponse])
def list_users(
    service: Annotated[UserService, Depends(get_user_service)],
) -> list[UserResponse]:
    users = service.list_users()

    return [UserResponse.model_validate(user) for user in users]

@router.get("/by-email", response_model=UserResponse)
def get_user_by_email(
    email: EmailStr,
    service: UserServiceDependency,   
) -> UserResponse:
    try:
        user = service.get_user_by_email(str(email))
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return UserResponse.model_validate(user)

@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: UUID,
    service: UserServiceDependency,   
) -> UserResponse:
    try:
        user = service.get_user_by_id(user_id)
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return UserResponse.model_validate(user)

@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    data: UserUpdate,
    service: UserServiceDependency,
) -> UserResponse:
    try:
        user = service.update_user(
            user_id,
            name=data.name,
            email=str(data.email) if data.email is not None else None,
        )
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_user(
    user_id: UUID,
    service: UserServiceDependency,
) -> Response:
    try:
        service.delete_user(user_id)
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)
