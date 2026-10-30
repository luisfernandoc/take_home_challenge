from threading import Lock
import httpx
from cachetools import TTLCache

from app.users.application.exceptions import (
    PokemonNotFoundError,
    PokemonProviderUnavailableError,
)

class PokeApiClient:
    def __init__(self, http_client: httpx.Client) -> None:
        self._http_client = http_client
        self._cache: TTLCache[int, str] = TTLCache(maxsize=1024, ttl=3600)
        self._cache_lock = Lock()

    def get_name_by_id(self, pokemon_id: int) -> str:
        if pokemon_id <= 0:
            raise ValueError("The ID of the Pokemon should be positive")

        with self._cache_lock:
            cached_name = self._cache.get(pokemon_id)

        if cached_name is not None:
            return cached_name

        try:
            response = self._http_client.get(
                f"pokemon/{pokemon_id}/"
            )
        except httpx.RequestError as error:
            raise PokemonProviderUnavailableError(
                "It was not possible to connect with PokeAPI"
            ) from error

        if response.status_code == 404:
            raise PokemonNotFoundError(
                f"Pokemon with ID {pokemon_id} does not exist."
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise PokemonProviderUnavailableError(
                "PokeApi returned a unexpected response."
            ) from error

        try:
            data = response.json()
        except ValueError as error:
            raise PokemonProviderUnavailableError(
                "PokeAPI returned an invalid JSON"
            ) from error

        if not isinstance(data, dict):
            raise PokemonProviderUnavailableError(
                "PokeAPI returned an unexpected structure"
            )

        name = data.get("name")

        if not isinstance(name, str) or not name.strip():
            raise PokemonProviderUnavailableError(
                "The response of PokeAPI does not contain a valid name"
            )

        with self._cache_lock:
            self._cache[pokemon_id] = name

        return name
