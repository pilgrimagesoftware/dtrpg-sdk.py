"""Mock-server tests for `token_refresh.refresh` and `sdk.refresh_session`."""

from __future__ import annotations

import httpx
import pytest
import respx

from dtrpg_sdk.auth.session import AuthTokenResponse
from dtrpg_sdk.auth.token_refresh import refresh
from dtrpg_sdk.config import Config
from dtrpg_sdk.errors import DecodeFailedError, UnauthenticatedError, UnconfiguredError
from dtrpg_sdk.sdk import DriveThruRpgSdk

REFRESH_URL = "http://testserver/api/vBeta/auth/refresh"
REFRESHED_BODY = {
    "token": "new-jwt",
    "refreshToken": "new-refresh",
    "refreshTokenTTL": 2_000_000_000,
}


@pytest.fixture
def config() -> Config:
    """A `Config` pointed at a fake local API host for mocking."""
    return Config(application_key="test-app-key", base_url="http://testserver/api")


@pytest.fixture
def sdk(config: Config) -> DriveThruRpgSdk:
    """An SDK holding a session that is due for a refresh."""
    sdk = DriveThruRpgSdk.with_config(config)
    sdk.apply_auth_response(AuthTokenResponse("old-jwt", "old-refresh", 1_000_000_000))
    return sdk


@respx.mock
def test_refresh_sends_token_as_cookie_and_decodes_response(config: Config) -> None:
    """The refresh token goes out as a `refreshToken` cookie; the body decodes."""
    route = respx.post(REFRESH_URL).mock(
        return_value=httpx.Response(200, json=REFRESHED_BODY)
    )

    response = refresh("old-refresh", config)

    assert route.calls.last.request.headers["cookie"] == "refreshToken=old-refresh"
    assert response.token == "new-jwt"
    assert response.refresh_token == "new-refresh"
    assert response.refresh_token_ttl == 2_000_000_000


@respx.mock
def test_refresh_reports_rejected_token_as_decode_failure_with_status(
    config: Config,
) -> None:
    """An error response surfaces as `DecodeFailedError` carrying the status."""
    respx.post(REFRESH_URL).mock(
        return_value=httpx.Response(401, json={"errorCode": "refresh_expired"})
    )

    with pytest.raises(DecodeFailedError) as exc_info:
        refresh("expired", config)

    assert exc_info.value.status == 401


@respx.mock
def test_refresh_session_replaces_the_stored_session(sdk: DriveThruRpgSdk) -> None:
    """A successful refresh swaps in the new token, refresh token, and expiry."""
    respx.post(REFRESH_URL).mock(return_value=httpx.Response(200, json=REFRESHED_BODY))

    session = sdk.refresh_session()

    assert session.token == "new-jwt"
    assert session.refresh_token == "new-refresh"
    assert session.refresh_token_ttl == 2_000_000_000
    assert sdk.session is session


@respx.mock
def test_refresh_session_keeps_the_old_session_when_rejected(
    sdk: DriveThruRpgSdk,
) -> None:
    """A rejected refresh leaves the existing session untouched."""
    respx.post(REFRESH_URL).mock(return_value=httpx.Response(401, text="{}"))

    with pytest.raises(DecodeFailedError):
        sdk.refresh_session()

    assert sdk.require_session().token == "old-jwt"


def test_refresh_session_requires_config_and_session(config: Config) -> None:
    """Refreshing without a config or a session raises the matching error."""
    with pytest.raises(UnconfiguredError):
        DriveThruRpgSdk().refresh_session()
    with pytest.raises(UnauthenticatedError):
        DriveThruRpgSdk.with_config(config).refresh_session()
