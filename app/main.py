from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.infrastructure.clients.pokeapi_client import PokeApiClient
from app.users.presentation.controller import router as users_router

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    with httpx.Client(
        base_url="https://pokeapi.co/api/v2/",
        timeout=5.0,
    ) as http_client:
        app.state.pokemon_client = PokeApiClient(
            http_client=http_client,
        )

        yield

app = FastAPI(
    title="Take Home Challenge",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(users_router)
