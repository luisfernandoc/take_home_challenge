from typing import Annotated, Self
from uuid import UUID
from pydantic import(
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    StrictInt,
    StringConstraints,
    field_validator,
    model_validator,
)

PokemonId = Annotated[
    StrictInt,
    Field(gt=0),
]

class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=100,
        ),
    ]
    email: EmailStr
    password: SecretStr = Field(
        min_length=4,
        max_length=128,
    )
    pokemon_ids: list[PokemonId] = Field(
        default_factory=list,
        max_length=100,
    )

    @field_validator("pokemon_ids")
    @classmethod
    def validate_unique_pokemon_ids(
        cls,
        value: list[int],
    ) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError(
                "The list can't have repeated IDs"
            )

        return value

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    pokemons: list[str]

class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=100,
        ),
    ] | None = None

    email: EmailStr | None = None

    pokemon_ids: list[PokemonId] | None = Field(
        default=None,
        max_length=100,
    )

    @field_validator("pokemon_ids")
    @classmethod
    def validate_unique_pokemon_ids(
        cls,
        value: list[int] | None,
    ) -> list[int] | None:
        if value is not None and len(value) != len(set(value)):
            raise ValueError(
                "La lista no puede contener IDs repetidos"
            )

        return value

    @model_validator(mode="after")
    def validate_changes(self) -> Self:
        if not self.model_fields_set:
            raise ValueError(
                "Debes enviar al menos un campo para actualizar"
            )

        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(
                    f"El campo '{field_name}' no puede ser null"
                )

        return self
