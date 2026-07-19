"""Mock-server tests for `dtrpg_sdk.auth.key_exchange.authenticate`."""

from __future__ import annotations

import httpx
import pytest
import respx

from dtrpg_sdk.auth.key_exchange import authenticate
from dtrpg_sdk.config import Config
from dtrpg_sdk.errors import DecodeFailedError


@pytest.fixture
def config() -> Config:
    """A `Config` pointed at a fake local API host for mocking."""
    return Config(application_key="test-app-key", base_url="http://testserver/api")


@respx.mock
def test_authenticate_returns_token_response_on_success(config: Config) -> None:
    """A successful `auth_key` response decodes into an `AuthTokenResponse`."""
    route = respx.post("http://testserver/api/vBeta/auth_key").mock(
        return_value=httpx.Response(
            200,
            json={
                "token": "jwt-token",
                "refreshToken": "refresh-token",
                "refreshTokenTTL": 999,
            },
        )
    )

    response = authenticate("test-app-key", config)

    assert route.called
    request = route.calls.last.request
    assert request.url.params["applicationKey"] == "test-app-key"
    assert response.token == "jwt-token"
    assert response.refresh_token == "refresh-token"
    assert response.refresh_token_ttl == 999


@respx.mock
def test_authenticate_raises_decode_failed_on_malformed_body(config: Config) -> None:
    """A success status with an undecodable body raises `DecodeFailedError`."""
    respx.post("http://testserver/api/vBeta/auth_key").mock(
        return_value=httpx.Response(200, text="not json")
    )

    with pytest.raises(DecodeFailedError) as exc_info:
        authenticate("test-app-key", config)

    assert exc_info.value.status == 200


@respx.mock
def test_authenticate_raises_decode_failed_on_missing_fields(config: Config) -> None:
    """A success status missing required fields raises `DecodeFailedError`."""
    respx.post("http://testserver/api/vBeta/auth_key").mock(
        return_value=httpx.Response(200, json={"token": "jwt-token"})
    )

    with pytest.raises(DecodeFailedError):
        authenticate("test-app-key", config)
