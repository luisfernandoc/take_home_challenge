from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TestDatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TEST_",
        extra="ignore",
    )

    postgres_db: str
    postgres_user: str
    postgres_password: SecretStr
    postgres_host: str
    postgres_port: int = Field(ge=1, le=65535)

    @field_validator("postgres_db")
    @classmethod
    def validate_test_database(cls, value: str) -> str:
        if not value.endswith("_test"):
            raise ValueError(
                "La base de pruebas debe terminar en '_test'"
            )

        return value


@lru_cache
def get_test_settings() -> TestDatabaseSettings:
    return TestDatabaseSettings()