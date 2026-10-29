from fastapi import FastAPI

from app.users.presentation.controller import router as users_router

app = FastAPI(
    title="Take Home Challenge",
    version="0.1.0",
)

app.include_router(users_router)
