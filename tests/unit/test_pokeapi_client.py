from unittest.mock import Mock

import httpx
import pytest

from app.users.application.exceptions import (
    PokemonNotFoundError,
    PokemonProviderUnavailableError,
)


def test_get_name_builds_expected_request_and_uses_cache(
    pokeapi_client_factory,
) -> None:
    handler = Mock(
        return_value=httpx.Response(
            200,
            json={"id": 25, "name": "pikachu"},
        )
    )
    client = pokeapi_client_factory(handler)

    assert client.get_name_by_id(25) == "pikachu"
    assert client.get_name_by_id(25) == "pikachu"

    handler.assert_called_once()

    request = handler.call_args.args[0]

    assert request.method == "GET"
    assert str(request.url) == ("https://pokeapi.test/api/v2/pokemon/25/")


def test_cache_keeps_names_separate_by_id(
    pokeapi_client_factory,
) -> None:
    handler = Mock(
        side_effect=[
            httpx.Response(200, json={"name": "bulbasaur"}),
            httpx.Response(200, json={"name": "pikachu"}),
        ]
    )
    client = pokeapi_client_factory(handler)

    assert client.get_name_by_id(1) == "bulbasaur"
    assert client.get_name_by_id(25) == "pikachu"
    assert client.get_name_by_id(1) == "bulbasaur"

    assert handler.call_count == 2


@pytest.mark.parametrize("pokemon_id", [0, -1])
def test_invalid_id_does_not_make_http_request(
    pokeapi_client_factory,
    pokemon_id: int,
) -> None:
    handler = Mock()
    client = pokeapi_client_factory(handler)

    with pytest.raises(ValueError):
        client.get_name_by_id(pokemon_id)

    handler.assert_not_called()


def test_404_becomes_pokemon_not_found(
    pokeapi_client_factory,
) -> None:
    handler = Mock(return_value=httpx.Response(404))
    client = pokeapi_client_factory(handler)

    with pytest.raises(PokemonNotFoundError):
        client.get_name_by_id(999999)


@pytest.mark.parametrize("status_code", [400, 429, 500, 503])
def test_other_http_errors_become_provider_unavailable(
    pokeapi_client_factory,
    status_code: int,
) -> None:
    handler = Mock(return_value=httpx.Response(status_code))
    client = pokeapi_client_factory(handler)

    with pytest.raises(PokemonProviderUnavailableError):
        client.get_name_by_id(25)


@pytest.mark.parametrize(
    "error_type",
    [
        httpx.ConnectError,
        httpx.ReadTimeout,
    ],
)
def test_network_errors_become_provider_unavailable(
    pokeapi_client_factory,
    error_type: type[httpx.RequestError],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error_type(
            "Fallo de red simulado",
            request=request,
        )

    client = pokeapi_client_factory(handler)

    with pytest.raises(PokemonProviderUnavailableError):
        client.get_name_by_id(25)


def test_invalid_json_becomes_provider_unavailable(
    pokeapi_client_factory,
) -> None:
    handler = Mock(
        return_value=httpx.Response(
            200,
            content=b"esto no es JSON",
        )
    )
    client = pokeapi_client_factory(handler)

    with pytest.raises(PokemonProviderUnavailableError):
        client.get_name_by_id(25)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"name": None},
        {"name": 25},
        {"name": ""},
        {"name": "   "},
    ],
)
def test_invalid_response_structure_is_rejected(
    pokeapi_client_factory,
    payload,
) -> None:
    handler = Mock(
        return_value=httpx.Response(
            200,
            json=payload,
        )
    )
    client = pokeapi_client_factory(handler)

    with pytest.raises(PokemonProviderUnavailableError):
        client.get_name_by_id(25)


def test_failed_response_is_not_cached(
    pokeapi_client_factory,
) -> None:
    handler = Mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json={"name": "pikachu"}),
        ]
    )
    client = pokeapi_client_factory(handler)

    with pytest.raises(PokemonProviderUnavailableError):
        client.get_name_by_id(25)

    assert client.get_name_by_id(25) == "pikachu"
    assert client.get_name_by_id(25) == "pikachu"

    assert handler.call_count == 2
