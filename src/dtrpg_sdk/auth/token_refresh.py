"""HTTP client for the DriveThruRPG token refresh endpoint.

`refresh` exchanges a refresh token for a new access token, so a session can
be extended without repeating the application-key exchange.

The refresh endpoint is not described by the bundled OpenAPI document. Its
shape is inferred from the `Set-Cookie` header on the `auth_key` response,
which scopes the `refreshToken` cookie to `/api/vBeta/auth/refresh`: the token
is sent back as that cookie, and the response is assumed to carry the same
payload as `auth_key`.
"""

from __future__ import annotations

import logging

import httpx

from dtrpg_sdk.auth.key_exchange import decode_token_response
from dtrpg_sdk.auth.session import AuthTokenResponse
from dtrpg_sdk.config import Config
from dtrpg_sdk.errors import HttpError

_logger = logging.getLogger(__name__)


def refresh(refresh_token: str, config: Config) -> AuthTokenResponse:
    """Exchanges a refresh token for a new access token.

    Posts to `POST /{api_version}/auth/refresh` with the token in a
    `refreshToken` cookie. On success, returns a new access token together
    with the refresh token and expiry the API now considers current; callers
    should store all three, because the API may rotate the refresh token.

    Raises:
        HttpError: On transport errors.
        DecodeFailedError: If the response body cannot be parsed, which
            includes an error response such as `401` for an expired or
            revoked refresh token.

    Examples:
        >>> config = Config(application_key="my-app-key")
        >>> response = refresh("my-refresh-token", config)  # doctest: +SKIP
        >>> response.token  # doctest: +SKIP
    """
    url = f"{config.base_url}/{config.api_version}/auth/refresh"

    _logger.debug("SDK request: POST %s", url)
    try:
        with httpx.Client() as client:
            response = client.post(
                url, headers={"Cookie": f"refreshToken={refresh_token}"}, json={}
            )
    except httpx.HTTPError as cause:
        raise HttpError(cause) from cause

    return decode_token_response(url, response)
