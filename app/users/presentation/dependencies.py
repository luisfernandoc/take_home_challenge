from functools import lru_cache
from app.users.application.service import UserService
from app.users.domain.repositories import UserRepository
from app.users.infrastructure.repositories import InMemoryUserRepository

@lru_cache
def get_user_repository() -> UserRepository:
    return InMemoryUserRepository()

def get_user_service() -> UserService:
    return UserService(repository=get_user_repository())
