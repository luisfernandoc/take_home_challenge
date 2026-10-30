from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.users.application.exceptions import (
    PokemonNotFoundError,
    PokemonProviderUnavailableError,
)
from app.users.domain.exceptions import (
    EmailAlreadyRegisteredError,
    UserNotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(UserNotFoundError)
    async def user_not_found(
        request: Request,
        error: UserNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": str(error)},
        )

    @app.exception_handler(EmailAlreadyRegisteredError)
    async def email_already_registered(
        request: Request,
        error: EmailAlreadyRegisteredError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": str(error)},
        )

    @app.exception_handler(PokemonNotFoundError)
    async def pokemon_not_found(
        request: Request,
        error: PokemonNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={
                "detail": "PokéAPI no reconoce uno de los IDs consultados"
            },
        )

    @app.exception_handler(PokemonProviderUnavailableError)
    async def pokemon_provider_unavailable(
        request: Request,
        error: PokemonProviderUnavailableError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={
                "detail": "No fue posible consultar PokéAPI"
            },
        )