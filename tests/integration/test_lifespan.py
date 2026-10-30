from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest

import app.main as main_module


pytestmark = pytest.mark.anyio


async def test_lifespan_creates_and_closes_pokeapi_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler = Mock(
        return_value=httpx.Response(
            200,
            json={"name": "pikachu"},
        )
    )

    http_client = httpx.Client(
        base_url="https://pokeapi.test/api/v2/",
        transport=httpx.MockTransport(handler),
    )

    client_factory = Mock(return_value=http_client)

    settings = SimpleNamespace(
        pokeapi_base_url="https://pokeapi.test/api/v2/",
    )

    monkeypatch.setattr(
        main_module,
        "get_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        main_module.httpx,
        "Client",
        client_factory,
    )

    try:
        async with main_module.app.router.lifespan_context(
            main_module.app
        ):
            assert not http_client.is_closed

            pokemon_client = (
                main_module.app.state.pokemon_client
            )

            assert pokemon_client.get_name_by_id(25) == "pikachu"
            assert pokemon_client.get_name_by_id(25) == "pikachu"

            handler.assert_called_once()

        assert http_client.is_closed
    finally:
        http_client.close()
