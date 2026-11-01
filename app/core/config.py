from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: SecretStr | None = None

    postgres_db: str | None = None
    postgres_user: str | None = None
    postgres_password: SecretStr | None = None
    postgres_host: str | None = None
    postgres_port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
    )
    pokeapi_base_url: str

    @model_validator(mode="after")
    def validate_database_configuration(self) -> Self:
        if self.database_url is not None:
            if not self.database_url.get_secret_value().strip():
                raise ValueError("DATABASE_URL cannot be empty")

            return self

        required_fields = (
            "postgres_db",
            "postgres_user",
            "postgres_password",
            "postgres_host",
            "postgres_port",
        )

        missing = [name for name in required_fields if getattr(self, name) is None]

        if missing:
            raise ValueError(
                f"Provide DATABASE_URL or all PostgreSQL settings. Missing: {', '.join(missing)}"
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
